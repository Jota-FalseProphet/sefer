# 07 - Deployment

> Status: **Draft** | Last updated: 2026-03-27

## Target

- **Host**: sachielNode (192.168.1.52)
- **User**: jota
- **Method**: Docker Compose
- **Port**: 2552

## Docker Setup

```yaml
# docker-compose.yml (draft)
version: "3.8"
services:
  sefer:
    build: .
    ports:
      - "2552:2552"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ODOO_SSH_HOST=${ODOO_SSH_HOST}
      - ODOO_SSH_USER=${ODOO_SSH_USER}
      - ODOO_CONTAINER_NAME=${ODOO_CONTAINER_NAME}
    volumes:
      - sefer-data:/app/data
      - ~/.ssh/id_ed25519:/app/.ssh/key:ro
    restart: unless-stopped

volumes:
  sefer-data:
```

## Environment Variables

| Variable              | Description                        | Required |
|-----------------------|------------------------------------|----------|
| ANTHROPIC_API_KEY     | Claude API key                     | Yes      |
| ODOO_SSH_HOST         | SSH host for Odoo server           | Yes      |
| ODOO_SSH_USER         | SSH user                           | Yes      |
| ODOO_SSH_KEY_PATH     | Path to SSH private key            | Yes      |
| ODOO_CONTAINER_NAME   | Docker container / K8s pod name    | Yes      |
| ODOO_CONTAINER_TYPE   | "docker" or "kubernetes"           | Yes      |
| SEFER_API_KEYS        | Comma-separated PM API keys        | Yes      |

## Deploy Flow

```
local dev → git push → ssh sachielNode
  → cd /home/jota/sefer
  → git pull
  → docker compose up -d --build
```

## Open Questions

- [ ] CI/CD pipeline or manual deploy?
- [ ] Log aggregation on sachielNode?
- [ ] Backup strategy for SQLite data volume?
