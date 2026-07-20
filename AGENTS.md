# Project rules — Robinhood Agentic Trading

## Purpose

This repository configures and documents Robinhood **Agentic Trading** via the official Trading MCP server.

- MCP URL: `https://agent.robinhood.com/mcp/trading`
- Config: `.grok/config.toml` → `[mcp_servers.robinhood-trading]`

## Using the integration

1. Ensure the `robinhood-trading` MCP server is enabled (`/mcps`).
2. If tools fail with auth errors, user must OAuth-authenticate (press `i` on the server in `/mcps`).
3. Discover tools with `search_tool` (e.g. query `"robinhood"` or `"trading"`).
4. Call tools with `use_tool` using the qualified name `robinhood-trading__<tool>`.

## Safety constraints for the agent

- **Only trade in the Agentic account.** Never attempt to move funds or place orders outside what the MCP allows.
- Prefer **read-only analysis** (positions, balances, quotes, thesis) unless the user explicitly asks to place or cancel orders.
- Before placing orders, **summarize** symbol, side, quantity/notional, order type, and estimated impact; confirm with the user when intent is ambiguous.
- Never invent balances, positions, or fill prices — always pull live data from MCP tools.
- Surface Robinhood risk disclosures when the user first enables trading automation.

## Active runbook

- Full process, Plan 1 (SMH), levels, and scheduled Tasks: see [README.md](README.md).
- Plan 1 automation may auto-sell SMH at stop **$536** or targets **$585 / $620** when Tasks fire; user opted into that automation.
- Email reports address: `sawaiz@sawaizsyed.com`.
- Fractional stops are not supported — never claim a resting stop is on the book without verifying open orders.

## Do not

- Store API keys, OAuth tokens, or account numbers in the repo.
- Commit credentials or `.env` files.
- Bypass user confirmation for large or irreversible portfolio changes when the user has not opted into fully autonomous execution.
