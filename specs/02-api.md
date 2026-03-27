# 02 - API Endpoints

> Status: **Draft** | Last updated: 2026-03-27

## Base URL

```
http://<host>:2552/api/v1
```

## Endpoints

### Chat

| Method | Path              | Description                    |
|--------|-------------------|--------------------------------|
| POST   | `/chat`           | Send a message, get a response |
| GET    | `/chat/history`   | List conversation history      |
| GET    | `/chat/{id}`      | Get a specific conversation    |
| DELETE | `/chat/{id}`      | Delete a conversation          |

### Health

| Method | Path        | Description          |
|--------|-------------|----------------------|
| GET    | `/health`   | Service health check |
| GET    | `/status`   | Odoo connection status |

### Tasks

| Method | Path        | Description                  |
|--------|-------------|------------------------------|
| GET    | `/tasks`    | List created tasks           |
| POST   | `/tasks`    | Create a task in Odoo        |

## Request/Response Contracts

### POST /chat

**Request:**
```json
{
  "message": "What modules are installed?",
  "session_id": "optional-session-uuid"
}
```

**Response:**
```json
{
  "response": "The following modules are installed on the instance: ...",
  "session_id": "uuid",
  "tools_used": ["odoo_shell"],
  "timestamp": "2026-03-27T10:00:00Z"
}
```

## Open Questions

- [ ] Streaming responses (SSE) for long operations?
- [ ] Rate limiting per user?
- [ ] Pagination for history endpoint?
