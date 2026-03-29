# Sefer - Development

## Project

Sefer is an AI-powered web manager for Product Managers. It wraps Claude Code CLI behind a FastAPI + chat UI so PMs can query Odoo environments without technical knowledge. Each user authenticates with their own Claude account via OAuth.

## Architecture

- **Backend**: FastAPI (src/main.py) on port 2552
- **Frontend**: Vanilla HTML/CSS/JS chat UI
- **AI**: Claude Code CLI executed as local subprocess per user
- **Auth**: Email + password + email verification (Resend), PostgreSQL-backed
- **Claude Auth**: Per-user OAuth via PTY REPL automation (data/claude-users/{id}/)
- **PM system prompt**: src/prompts/sefer_system.md (passed via --system-prompt to Claude Code)

## Key Files

- src/main.py - FastAPI app, static routes
- src/api/routes.py - API endpoints (auth, chat, Claude OAuth)
- src/core/claude_runner.py - PTY REPL login + subprocess runner for Claude CLI
- src/core/auth.py - User auth, verification codes, PostgreSQL
- src/core/email.py - Email verification via Resend SDK
- src/core/logging.py - Dual logging (server.log + claude.log)
- src/config.py - Settings from env vars
- src/prompts/sefer_system.md - System prompt for PM-facing Claude
- src/templates/login.html - Login/register with email verification
- src/templates/connect-claude.html - Per-user Claude OAuth flow
- src/templates/index.html - Chat UI

## Infrastructure

- **Docker Compose**: db (PostgreSQL 17), odoo, sefer, nginx
- **Nginx**: reverse proxy for subdomain routing
- **Cloudflare Tunnel**: public access behind NAT (systemd service)
- **Resend**: transactional email from noreply@yostesis.online

## URLs

- sefer.yostesis.online - Sefer chat UI
- akua.yostesis.online - Odoo 15 (EpistolaGenesis)

## Deploy

- **Host**: sachielNode (192.168.1.52, EndeavourOS)
- **Method**: Docker Compose + Cloudflare Tunnel
- **Domain**: yostesis.online (Namecheap, DNS on Cloudflare)
- **Guide**: specs/07-deployment.md

### Deploy commands

```bash
ssh jota@192.168.1.52
cd /home/jota/sefer
git pull
sudo docker compose build sefer
sudo docker compose up -d sefer
sudo docker compose logs sefer -f --tail 20
```

## User flow

1. Register (email + password + confirm) -> verification code via email
2. Connect Claude (OAuth: URL -> authenticate -> paste code)
3. Chat with Sefer (Claude Code queries EpistolaGenesis read-only)

## Claude OAuth (PTY REPL)

Each user's Claude credentials are stored in `data/claude-users/{user_id}/`. The OAuth flow works by:

1. Starting a Claude REPL in a PTY with `CLAUDE_CONFIG_DIR` set per user
2. Auto-completing the setup wizard (theme + login method)
3. Extracting the OAuth URL (stripping terminal line-wraps)
4. User visits URL, authenticates, gets code
5. Code is written to PTY via bracketed paste mode
6. REPL exchanges code for tokens, saves to `.credentials.json`

Key: codes expire fast (~60s), so the wizard must complete quickly.

## Environment variables

| Variable | Description |
|----------|-------------|
| RESEND_API_KEY | Resend API key for email verification |
| DATABASE_URL | PostgreSQL connection string |
| SEFER_CLAUDE_CWD | Working directory for Claude CLI |
| SEFER_MODEL | Claude model (default: sonnet) |

## Database

- **PostgreSQL 17** (shared with Odoo)
- DB name: `sefer`, user: `sefer`
- Tables: users, sessions, verification_codes
- Init script: docker/db/init-sefer-db.sh

## Odoo (EpistolaGenesis)

- Odoo 15 on Python 3.12
- DB imported from local `baseDatos`
- Config: EpistolaGenesis/conf/odoo-docker.conf
- Custom modules in modulos/modulos-terceros (need pandas, numpy, phonenumbers)
- PG 18 dump compatibility: required patching NOT NULL syntax for ir_act_* tables
