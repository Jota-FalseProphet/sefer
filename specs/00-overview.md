# Sefer - Overview

## What is Sefer?

Sefer is an AI-powered operations assistant for **Product Managers/Owners** working with a single Odoo instance. It runs as a self-hosted service on port **2552** and allows PMs to ask questions in natural language. Claude answers by connecting to the target Odoo environment (Docker or Kubernetes), inspecting state, querying data, and producing actionable results.

## The Problem

PMs need answers that live inside a running Odoo instance:
- "What modules are installed on staging?"
- "Show me the last 50 error logs"
- "What's the current stock configuration for warehouse X?"
- "Create a task for the devs to fix the invoice workflow"

Today, PMs ask devs. Devs SSH in, run `docker exec` or `kubectl exec`, dig through Odoo shells, and report back. This is slow and interrupts dev work.

## The Solution

Sefer gives PMs a direct channel to Claude, which has **tools** to:

1. **Connect to the Odoo container** via SSH + `docker exec` / `kubectl exec`
2. **Run read-only queries** (Odoo shell ORM, SQL SELECTs, log inspection)
3. **Synthesize answers** in PM-friendly language
4. **Create tasks** for the dev team when action is needed

### Scope

- **One Odoo instance per Sefer deployment** (not multi-tenant)
- **Read-only** for inspection operations
- **Write** only for task/ticket creation within Odoo
- **Memory** to retain context across PM conversations

## Target Environment

| Property         | Value                                |
|------------------|--------------------------------------|
| Language          | Python (FastAPI)                    |
| AI Backend        | Claude API (Anthropic)              |
| Port              | 2552                                |
| Deploy            | Docker on sachielNode (192.168.1.52)|
| Odoo Connection   | SSH → docker exec / kubectl exec    |

## Architecture

```
┌──────────────────────────────────────┐
│         Product Managers             │
│       (browser / chat UI)            │
└─────────────┬────────────────────────┘
              │ HTTP :2552
┌─────────────▼────────────────────────┐
│          FastAPI Gateway             │
├──────────────────────────────────────┤
│          Core Engine                 │
│  ┌─────────┐ ┌────────┐ ┌────────┐  │
│  │  Chat   │ │ Memory │ │ Agents │  │
│  └─────────┘ └────────┘ └────────┘  │
├──────────────────────────────────────┤
│          Tools                       │
│  ┌────────────────┐ ┌────────────┐  │
│  │ Odoo Connector │ │ Task Maker │  │
│  │ (SSH+exec, RO) │ │ (write)    │  │
│  └────────────────┘ └────────────┘  │
├──────────────────────────────────────┤
│          Claude API                  │
└──────────┬───────────────────────────┘
           │ SSH
     ┌─────▼──────┐
     │ Odoo Host  │
     │ (Docker/K8s│
     │  container)│
     └────────────┘
```

## Spec Documents

| #  | Document                              | Description                            | Status |
|----|---------------------------------------|----------------------------------------|--------|
| 01 | [architecture.md](01-architecture.md) | Components, data flow, tech decisions  | Draft  |
| 02 | [api.md](02-api.md)                   | HTTP API endpoints & contracts         | Draft  |
| 03 | [memory.md](03-memory.md)             | Conversation history & context         | Draft  |
| 04 | [agents.md](04-agents.md)             | Agent roles & orchestration            | Draft  |
| 05 | [tools.md](05-tools.md)               | Odoo connector, task creator, etc.     | Draft  |
| 06 | [security.md](06-security.md)         | Auth, read-only enforcement, audit     | Draft  |
| 07 | [deployment.md](07-deployment.md)     | Docker build & sachielNode deploy      | Draft  |
| 08 | [development.md](08-development.md)   | Dev workflow, testing                  | Draft  |
