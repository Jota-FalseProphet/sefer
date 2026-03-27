# 08 - Development

> Status: **Draft** | Last updated: 2026-03-27

## Project Structure

```
sefer/
├── specs/              # SDD specs (this folder)
├── src/
│   ├── main.py         # FastAPI entrypoint
│   ├── config.py       # Configuration
│   ├── api/            # Route handlers
│   ├── core/           # Chat manager, memory, orchestrator
│   ├── agents/         # Agent definitions
│   ├── tools/          # Tool implementations
│   └── models/         # Data models (Pydantic)
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Dev Workflow

1. Develop locally on Windows (F:\sefer)
2. Test with mock Odoo connector (no real SSH needed)
3. Push to GitHub
4. Deploy to sachielNode via Docker

## Testing Strategy

- **Unit tests**: Tool validation, command sanitization, memory operations
- **Integration tests**: Claude API calls with mock tools
- **E2E tests**: Full flow against a test Odoo container (optional)

## Local Dev

```bash
# Setup
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run
uvicorn src.main:app --host 0.0.0.0 --port 2552 --reload

# Test
pytest tests/
```

## Open Questions

- [ ] Pre-commit hooks (ruff, mypy)?
- [ ] GitHub Actions CI?
- [ ] Dev container / devcontainer.json?
