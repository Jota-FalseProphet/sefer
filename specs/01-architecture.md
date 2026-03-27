# 01 - Architecture

> Status: **Draft** | Last updated: 2026-03-27

## Components

### FastAPI Gateway
- HTTP server on port 2552
- Session management
- Request routing to core engine

### Core Engine
- **Chat Manager**: Manages conversation flow, sends messages to Claude API
- **Memory Store**: Persists conversation history and extracted context
- **Agent Orchestrator**: Routes queries to specialized agents

### Tools
- **Odoo Connector**: SSH → docker exec / kubectl exec (read-only)
- **Task Maker**: Creates tasks/tickets in Odoo (the only write operation)

### Claude API Integration
- Model: configurable (default: claude-sonnet-4-6 for cost efficiency)
- Adaptive thinking enabled
- Tool use with agentic loop

## Data Flow

```
PM question
  → Gateway (auth, session)
    → Chat Manager (build prompt + history)
      → Claude API (with tools)
        → Tool call: Odoo Connector
          → SSH → docker exec → odoo shell / psql / logs
          → Result (read-only data)
        → Claude synthesizes answer
      → Memory Store (save exchange)
    → Response to PM
```

## Tech Stack

| Component     | Technology              |
|---------------|------------------------|
| Framework      | FastAPI                |
| AI SDK         | anthropic (Python)     |
| SSH            | paramiko / asyncssh    |
| Database       | SQLite (memory store)  |
| Containerization | Docker + Compose     |

## Open Questions

- [ ] SQLite vs PostgreSQL for memory store?
- [ ] WebSocket for streaming responses or SSE?
- [ ] Authentication method for PMs (API key, basic auth, OAuth)?
