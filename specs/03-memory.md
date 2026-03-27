# 03 - Memory System

> Status: **Draft** | Last updated: 2026-03-27

## Purpose

Retain conversation context so PMs don't have to re-explain their setup or repeat questions. Memory enables Claude to reference past interactions and build understanding over time.

## Layers

### 1. Conversation History
- Full message log per session
- Stored in SQLite
- Used to rebuild Claude's context on each request

### 2. Session Context
- Extracted facts from conversations (e.g., "client uses warehouse module v16")
- Persists across sessions
- Fed to Claude as system prompt context

### 3. Environment Snapshot
- Cached state of the Odoo instance (installed modules, version, etc.)
- Refreshed periodically or on-demand
- Avoids repeated SSH calls for static info

## Storage

| Data               | Store   | TTL              |
|--------------------|---------|------------------|
| Messages           | SQLite  | Indefinite       |
| Session context    | SQLite  | Indefinite       |
| Environment cache  | SQLite  | Configurable (1h)|

## Open Questions

- [ ] Max conversation length before compaction?
- [ ] How to handle conflicting context across sessions?
- [ ] Export/import of memory data?
