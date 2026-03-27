# 05 - Tools

> Status: **Draft** | Last updated: 2026-03-27

## Purpose

Tools are the capabilities Claude can invoke to interact with the real world. Each tool is registered in the Tool Registry and exposed to Claude via the tool_use API.

## Tool Catalog

### odoo-shell
- **Type**: Read-only
- **Description**: Execute Odoo shell commands (ORM queries)
- **Connection**: SSH → docker exec → odoo shell -c "..."
- **Safety**: Commands are validated; only `env['model'].search/read/browse` allowed
- **Example**: `env['ir.module.module'].search_read([('state','=','installed')], ['name','installed_version'])`

### odoo_logs
- **Type**: Read-only
- **Description**: Read Odoo container logs
- **Connection**: SSH → docker logs <container> --tail N
- **Safety**: Tail-only, no log modification

### odoo_psql
- **Type**: Read-only
- **Description**: Run SELECT queries against the Odoo PostgreSQL database
- **Connection**: SSH → docker exec → psql -c "SELECT ..."
- **Safety**: Only SELECT statements allowed; validated before execution

### system_info
- **Type**: Read-only
- **Description**: Get container/pod status, resource usage, uptime
- **Connection**: SSH → docker ps / kubectl get pods

### create_task
- **Type**: Write
- **Description**: Create a task in Odoo's project module
- **Connection**: SSH → odoo shell → `env['project.task'].create({...})`
- **Safety**: Only creates tasks; cannot modify existing records

## Security Model

```
Tool input (from Claude)
  → Validate: is command read-only?
  → Validate: matches allowed patterns?
  → Execute via SSH
  → Sanitize output (strip credentials, tokens)
  → Return to Claude
```

## Open Questions

- [ ] Allowlist of Odoo models for odoo_shell?
- [ ] Max output size from tools?
- [ ] Timeout per tool execution?
