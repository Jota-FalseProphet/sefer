"""
Runs Claude Code CLI locally as a subprocess.
Streams results back as they arrive.
"""

import asyncio
import json
from typing import AsyncGenerator

from src.config import settings
from src.core.logging import claude_log


async def run_claude_stream(prompt: str, session_id: str | None = None) -> AsyncGenerator[dict, None]:
    cmd = [
        settings.claude_bin,
        "--print",
        "--output-format", "stream-json",
        "--verbose",
        "--model", settings.claude_model,
        "--dangerously-skip-permissions",
    ]

    if session_id:
        cmd.extend(["--resume", session_id])

    cmd.extend(["-p", prompt])

    claude_log.info(">>> PROMPT: %s", prompt)
    claude_log.debug(">>> CMD: %s", " ".join(cmd))

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=settings.claude_cwd,
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
    else:
        claude_log.debug("<<< EVENT [%s]: %s", etype, json.dumps(event)[:200])


async def run_claude_sync(prompt: str) -> str:
    full_text = ""
    async for event in run_claude_stream(prompt):
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
