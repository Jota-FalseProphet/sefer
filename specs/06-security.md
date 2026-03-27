# 06 - Security

> Status: **Draft** | Last updated: 2026-03-27

## Principles

1. **Read-only by default**: All inspection tools are strictly read-only
2. **Write is explicit**: Only `create_task` can write, and only to `project.task`
3. **Audit everything**: Every tool invocation is logged
4. **Least privilege**: SSH key used has minimal permissions

## Authentication

### PM Access to Sefer
- API key per user (header: `X-API-Key`)
- Keys stored hashed in config/database

### Sefer Access to Odoo Host
- Dedicated SSH key (read-only user on Odoo host)
- Key stored in Docker secret / env var
- No root access; limited to docker exec / kubectl exec

## Command Validation

Before executing any tool command:

1. **Allowlist check**: Command must match known safe patterns
2. **SQL validation**: Only `SELECT` statements (no INSERT/UPDATE/DELETE/DROP)
3. **ORM validation**: Only `.search()`, `.read()`, `.browse()`, `.search_read()`, `.search_count()`
4. **Output sanitization**: Strip passwords, tokens, API keys from output

## Audit Log

Every tool invocation records:
- Timestamp
- User (PM)
- Tool name
- Input command
- Output (truncated)
- Success/failure

## Open Questions

- [ ] Rate limiting per PM?
- [ ] IP allowlist for Sefer access?
- [ ] Rotate SSH keys automatically?
