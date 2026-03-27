from pydantic import BaseModel
import os


class Settings(BaseModel):
    port: int = 2552
    host: str = "0.0.0.0"

    # Claude Code binary (local)
    claude_bin: str = os.getenv("SEFER_CLAUDE_BIN", "claude")

    # Working directory for Claude Code
    claude_cwd: str = os.getenv("SEFER_CLAUDE_CWD", "F:/sefer")

    # Claude model
    claude_model: str = os.getenv("SEFER_MODEL", "sonnet")


settings = Settings()
