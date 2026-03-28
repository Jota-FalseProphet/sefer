# Sefer - Development

## Project

Sefer is an AI-powered web manager for Product Managers. It wraps Claude Code CLI behind a FastAPI + chat UI so PMs can query Odoo environments without technical knowledge.

## Architecture

- **Backend**: FastAPI (src/main.py) on port 2552
- **Frontend**: Vanilla HTML/CSS/JS chat UI
- **AI**: Claude Code CLI executed as local subprocess
- **Auth**: Email + password, SQLite-backed
- **PM system prompt**: src/prompts/sefer_system.md (passed via --system-prompt to Claude Code)

## Key Files

- src/main.py - FastAPI app
- src/api/routes.py - API endpoints
- src/core/claude_runner.py - Subprocess runner for Claude Code CLI
- src/core/auth.py - User auth
- src/core/logging.py - Dual logging (server.log + claude.log)
- src/prompts/sefer_system.md - System prompt for PM-facing Claude

## Deploy

- Dev: localhost (Windows)
- Prod: Docker on sachielNode (192.168.1.52)
- Odoo test env: EpistolaGenesis
