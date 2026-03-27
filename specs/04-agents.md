# 04 - Agents

> Status: **Draft** | Last updated: 2026-03-27

## Purpose

Specialized agents handle different types of PM queries. The orchestrator routes to the right agent based on intent.

## Agent Types

### Inspector Agent
- **Role**: Query Odoo state (modules, configs, data)
- **Tools**: Odoo Connector (read-only)
- **Example**: "What version of the stock module is installed?"

### Log Analyst Agent
- **Role**: Read and analyze logs
- **Tools**: Odoo Connector (log access)
- **Example**: "Show me errors from the last 24 hours"

### Task Creator Agent
- **Role**: Create tasks/tickets for the dev team
- **Tools**: Task Maker (write to Odoo project module)
- **Example**: "Create a task to fix the invoice rounding issue"

### General Agent
- **Role**: Answer general Odoo/business questions using memory + context
- **Tools**: Memory Store
- **Example**: "What did we discuss last week about the warehouse config?"

## Orchestration

```
PM query → Intent classification (Claude)
  → Route to appropriate agent
    → Agent executes with its tools
      → Response synthesized
```

## Open Questions

- [ ] Should agents be Claude tool-use loops or separate Claude calls?
- [ ] Agent-to-agent communication needed?
- [ ] Custom agent definitions by the team?
