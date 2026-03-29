# Sefer

AI-powered operations assistant for Product Managers working with Odoo. Sefer wraps Claude Code CLI behind a web chat interface, letting non-technical users query and inspect Odoo environments using natural language.

## How it works

Sefer acts as a bridge between Product Managers and their Odoo environment. Users ask questions in plain language, and Sefer uses Claude Code to read configs, search code, check logs, and report back — all read-only, no destructive actions.

```
PM question → Sefer → Claude Code CLI → Odoo environment → Answer
```

Each user authenticates with their own Claude account (OAuth). Sefer manages per-user credentials and runs isolated Claude sessions.

## Features

- **Chat UI** — Clean web interface for conversational queries
- **Email verification** — Secure registration with verification codes via Resend
- **Per-user Claude auth** — Each user connects their own Claude account via OAuth
- **Read-only access** — Claude is restricted to Read, Glob, Grep tools only
- **Streaming responses** — Real-time SSE streaming as Claude processes queries
- **Odoo-aware** — System prompt tuned for PM questions about Odoo

## Architecture

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python) |
| Frontend | Vanilla HTML/CSS/JS |
| AI | Claude Code CLI (subprocess) |
| Auth | PostgreSQL + Resend email |
| Proxy | Nginx (subdomain routing) |
| Infra | Docker Compose + Cloudflare Tunnel |

## Quick start

### Prerequisites

- Docker and Docker Compose
- A domain with DNS on Cloudflare
- [Resend](https://resend.com) account (free tier) for email verification

### Setup

```bash
git clone https://github.com/Jota-FalseProphet/sefer.git
cd sefer
cp .env.example .env
# Edit .env with your RESEND_API_KEY
```

### Run

```bash
docker compose up -d --build
```

Services:

| Service | Port | Description |
|---------|------|-------------|
| `sefer` | 2552 | FastAPI app |
| `odoo` | 8069 | Odoo 15 |
| `db` | 5432 | PostgreSQL 17 |
| `nginx` | 80 | Reverse proxy |

### Public access (optional)

For public access behind NAT, set up a [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/):

```bash
cloudflared tunnel create sefer
cloudflared tunnel route dns sefer your-subdomain.example.com
```

See `specs/07-deployment.md` for the full deployment guide.

## User flow

1. **Register** — Email + password, verification code sent via email
2. **Connect Claude** — OAuth flow to link your Claude account
3. **Chat** — Ask questions about your Odoo environment

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `RESEND_API_KEY` | Yes | Resend API key for email verification |
| `POSTGRES_PASSWORD` | No | PostgreSQL password (default: `odoo`) |
| `SEFER_MODEL` | No | Claude model (default: `sonnet`) |

## Project structure

```
sefer/
├── src/
│   ├── main.py              # FastAPI app
│   ├── config.py             # Settings
│   ├── api/routes.py         # API endpoints
│   ├── core/
│   │   ├── auth.py           # User auth (PostgreSQL)
│   │   ├── claude_runner.py  # Claude CLI runner + OAuth
│   │   ├── email.py          # Email via Resend
│   │   └── logging.py        # Dual logging
│   ├── prompts/              # System prompts
│   ├── templates/            # HTML pages
│   └── static/               # CSS
├── EpistolaGenesis/          # Odoo 15 instance
├── docker-compose.yml
├── Dockerfile
└── nginx/default.conf
```

## License

Private repository.
