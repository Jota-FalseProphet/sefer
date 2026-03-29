"""
Runs Claude Code CLI locally as a subprocess.
Streams results back as they arrive.
Multi-user: each user authenticates via OAuth through the Claude REPL.
"""

import asyncio
import json
import os
import pty
import re
import select
import time
from pathlib import Path
from typing import AsyncGenerator

from src.config import settings
from src.core.logging import claude_log

SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "sefer_system.md"
CLAUDE_USERS_DIR = Path(__file__).parent.parent.parent / "data" / "claude-users"

# Active login sessions: user_id -> (master_fd, pid)
_login_sessions: dict[int, tuple[int, int]] = {}


def _user_claude_home(user_id: int) -> Path:
    path = CLAUDE_USERS_DIR / str(user_id)
    path.mkdir(parents=True, exist_ok=True)
    # Pre-create settings so the REPL skips the setup wizard
    settings_file = path / "settings.json"
    if not settings_file.exists():
        settings_file.write_text('{}')
    return path


def _user_env(user_id: int) -> dict:
    env = os.environ.copy()
    env["CLAUDE_CONFIG_DIR"] = str(_user_claude_home(user_id))
    env["TERM"] = "dumb"
    env["COLUMNS"] = "5000"
    env["LINES"] = "40"
    return env


def _read_pty(master: int, timeout: float = 2) -> str:
    output = ""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if select.select([master], [], [], 0.2)[0]:
            try:
                data = os.read(master, 8192).decode("utf-8", errors="replace")
                output += data
            except OSError:
                break
    return output


def _clean_ansi(text: str) -> str:
    text = re.sub(r'\x1b\[[^a-zA-Z]*[a-zA-Z]', '', text)
    text = re.sub(r'\x1b\[\?[0-9]+[hl]', '', text)
    return text.replace('\r', '')


def _cleanup_login(user_id: int):
    session = _login_sessions.pop(user_id, None)
    if session:
        master, pid = session
        try:
            os.close(master)
        except OSError:
            pass
        try:
            os.kill(pid, 9)
        except ProcessLookupError:
            pass


def start_claude_login(user_id: int) -> str | None:
    """Start the Claude REPL, complete setup wizard, and return OAuth URL."""
    import subprocess

    _cleanup_login(user_id)

    env = _user_env(user_id)
    master, slave = pty.openpty()

    proc = subprocess.Popen(
        [settings.claude_bin],
        stdin=slave, stdout=slave, stderr=slave,
        env=env,
    )
    os.close(slave)

    try:
        # Wait for the REPL to start — press Enter quickly on any menu
        output = ""
        for _ in range(30):  # up to 15s (30 * 0.5s)
            chunk = _read_pty(master, 0.5)
            output += chunk
            cl = _clean_ansi(output).lower()
            if 'https://claude.com' in cl:
                # Read a bit more to get the full URL
                output += _read_pty(master, 2)
                break
            if any(w in cl for w in ['select', 'choose', 'login', 'theme', 'looks best']):
                os.write(master, b'\r')
                time.sleep(0.3)
        clean = _clean_ansi(output)

        # Extract URL — terminal wraps long lines with \n but we need the full URL.
        # The URL is followed by blank lines and "Paste code here if prompted"
        url = None
        idx = clean.find('https://claude.com')
        if idx >= 0:
            # Find the end: two consecutive newlines mark end of URL block
            end_idx = clean.find('\n\n', idx)
            if end_idx == -1:
                end_idx = len(clean)
            url_block = clean[idx:end_idx]
            # Remove line-wrapping whitespace within the URL
            url = re.sub(r'\s+', '', url_block)

        if url and proc.poll() is None:
            _login_sessions[user_id] = (master, proc.pid)
            claude_log.info("REPL login started for user %d", user_id)
            return url
        else:
            claude_log.warning("Failed to get OAuth URL for user %d. Output: %s", user_id, clean[:300])
            proc.kill()
            os.close(master)
            return None

    except Exception as e:
        claude_log.error("Error starting login for user %d: %s", user_id, str(e))
        proc.kill()
        os.close(master)
        return None


def submit_oauth_code(user_id: int, code: str) -> bool:
    """Paste the OAuth code into the waiting REPL."""
    session = _login_sessions.get(user_id)
    if not session:
        claude_log.warning("No login session for user %d", user_id)
        return False

    master, pid = session

    try:
        # Write the code. Use bracketed paste mode to avoid char-by-char echo issues.
        clean_code = code.strip()
        claude_log.info("Writing OAuth code for user %d: len=%d code=%s",
                       user_id, len(clean_code), clean_code)
        # Bracketed paste: tell terminal this is pasted content
        os.write(master, b'\x1b[200~')
        os.write(master, clean_code.encode())
        os.write(master, b'\x1b[201~')
        time.sleep(0.1)
        os.write(master, b'\r')
        claude_log.info("OAuth code written for user %d", user_id)

        # Wait for the REPL to process — it needs time to exchange the OAuth code
        # and show the welcome screen. Read in chunks, looking for indicators.
        full_output = ""
        for _ in range(24):  # up to 60s (24 * 2.5s)
            chunk = _read_pty(master, 2.5)
            full_output += chunk
            clean = _clean_ansi(full_output).lower()
            # Success: REPL shows welcome screen or prompt after auth
            if any(w in clean for w in ['welcome', 'claude code', 'tipscost']):
                claude_log.info("Login success detected for user %d", user_id)
                break
            if any(w in clean for w in ['error', 'failed', 'invalid code', 'expired']):
                claude_log.warning("Login failure detected for user %d: %s", user_id, clean[:200])
                break

        claude_log.info("REPL response for user %d: %s", user_id, _clean_ansi(full_output)[:500])

        # Give it time to write credentials to disk
        time.sleep(3)

        _cleanup_login(user_id)

        # Check if authentication succeeded
        return check_claude_auth_sync(user_id)

    except Exception as e:
        claude_log.error("Error submitting code for user %d: %s", user_id, str(e))
        _cleanup_login(user_id)
        return False


def check_claude_auth_sync(user_id: int) -> bool:
    """Check if user has valid Claude authentication by checking credentials file."""
    creds_file = _user_claude_home(user_id) / ".credentials.json"
    if creds_file.exists():
        try:
            import json as _json
            data = _json.loads(creds_file.read_text())
            has_token = bool(data.get("claudeAiOauth", {}).get("accessToken"))
            claude_log.debug("Auth check for user %d: creds=%s", user_id, has_token)
            return has_token
        except Exception:
            pass
    return False


async def check_claude_auth(user_id: int) -> bool:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, check_claude_auth_sync, user_id)


async def run_claude_stream(
    prompt: str,
    session_id: str | None = None,
    user_id: int | None = None,
) -> AsyncGenerator[dict, None]:
    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

    cmd = [
        settings.claude_bin,
        "--print",
        "--output-format", "stream-json",
        "--verbose",
        "--model", settings.claude_model,
        "--system-prompt", system_prompt,
        "--allowedTools", "Read", "Glob", "Grep", "WebSearch", "WebFetch",
    ]

    if session_id:
        cmd.extend(["--resume", session_id])

    cmd.extend(["-p", prompt])

    env = _user_env(user_id) if user_id else None

    claude_log.info(">>> PROMPT (user=%s): %s", user_id, prompt)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=settings.claude_cwd,
            env=env,
        )

        claude_log.info("Process started (PID %d)", proc.pid)

        buffer = ""
        while True:
            chunk = await proc.stdout.read(4096)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    _log_event(event)
                    yield event
                except json.JSONDecodeError:
                    claude_log.warning("Bad JSON line: %s", line[:200])

        await proc.wait()

        if proc.returncode and proc.returncode != 0:
            stderr_out = (await proc.stderr.read()).decode("utf-8", errors="replace").strip()
            claude_log.error("<<< STDERR (exit %d): %s", proc.returncode, stderr_out)
            yield {"type": "error", "error": stderr_out}
        else:
            claude_log.info("<<< Process finished OK (exit 0)")

    except Exception as e:
        claude_log.error("Unexpected error: %s", str(e), exc_info=True)
        yield {"type": "error", "error": f"Unexpected error: {str(e)}"}


def _log_event(event: dict):
    etype = event.get("type", "unknown")
    if etype == "assistant":
        content = event.get("message", {}).get("content", [])
        for block in content:
            if block.get("type") == "text":
                claude_log.info("<<< TEXT: %s", block.get("text", "")[:300])
            elif block.get("type") == "tool_use":
                claude_log.info("<<< TOOL_USE: %s(%s)", block.get("name"), json.dumps(block.get("input", {}))[:200])
    elif etype == "result":
        claude_log.info("<<< RESULT (session=%s): %s", event.get("session_id", "?"), str(event.get("result", ""))[:300])
    elif etype == "error":
        claude_log.error("<<< ERROR: %s", event.get("error", "unknown"))


async def run_claude_sync(prompt: str, user_id: int | None = None) -> str:
    full_text = ""
    async for event in run_claude_stream(prompt, user_id=user_id):
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "text":
                    full_text += block.get("text", "")
        elif event.get("type") == "result":
            result_text = event.get("result", "")
            if result_text and not full_text:
                full_text = result_text
        elif event.get("type") == "error":
            return f"Error: {event.get('error', 'unknown')}"
    return full_text
