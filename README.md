# Robinhood Agentic Trading

Integration with [Robinhood Agentic Trading](https://robinhood.com/us/en/agentic-trading/) via the official **Robinhood Trading MCP** server.

Announced by [@RobinhoodApp](https://x.com/RobinhoodApp): *“Robinhood is now open to AI agents.”* Connect an AI agent through Model Context Protocol (MCP), open a dedicated Agentic account, and let the agent research, trade equities/options, and manage a portfolio on your behalf.

## MCP endpoint

```
https://agent.robinhood.com/mcp/trading
```

| Capability | Status |
|---|---|
| Equities | Live |
| Options | Live |
| Crypto | Coming soon |
| Availability | Free for US-based Robinhood customers |

## Setup (Grok Build TUI)

This repo already includes project-scoped MCP config at [`.grok/config.toml`](.grok/config.toml). The same server is also registered in your user config (`~/.grok/config.toml`).

### 1. Authenticate (OAuth)

Robinhood’s MCP requires OAuth. From a Grok session in this directory:

1. Run `/mcps` (or open MCP Servers via the plugins panel).
2. Select **robinhood-trading**.
3. Press **`i`** to authenticate — Grok opens a browser OAuth flow.
4. Sign in with your Robinhood account and complete Agentic account onboarding **on desktop** (required by Robinhood).

You can also verify connectivity from the CLI:

```bash
grok mcp doctor robinhood-trading
```

After auth succeeds, doctor should report the server as healthy.

### 2. Open & fund an Agentic account

During MCP authentication Robinhood prompts you to open a dedicated **Agentic** account. Fund only what you want the agent to trade with. The agent:

- **Can read** balances, positions, orders, watchlists across your Robinhood accounts
- **Can only place trades** in the Agentic account
- Sends a **push notification** on every trade; real-time P&amp;L is visible in the Robinhood app
- Can be **disconnected anytime** from the app

### 3. Use it

Once connected, ask Grok things like:

- “What’s my Agentic account buying power and current positions?”
- “Build a thesis for NVDA and outline a dollar-cost averaging plan.”
- “Rebalance my Agentic portfolio toward 60% tech / 40% defensive.”

Tools appear as `robinhood-trading__*` after discovery via `search_tool`.

## Other platforms

Same MCP URL works elsewhere:

| Platform | How to connect |
|---|---|
| **Claude Code** | `claude mcp add robinhood-trading --transport http https://agent.robinhood.com/mcp/trading` |
| **Claude Desktop** | Settings → Connectors → Add custom connector → paste MCP URL |
| **ChatGPT** | Developer Mode → Settings → Apps → Create app → paste MCP URL |
| **Codex CLI** | `codex mcp add robinhood-trading --url https://agent.robinhood.com/mcp/trading` |
| **Cursor** | Settings → Tools & MCPs → Connect → paste MCP URL |
| **Grok (web)** | + → Add connector → Custom → paste MCP URL |

Official overview: [Agentic Trading overview](https://robinhood.com/us/en/support/articles/agentic-trading-overview/)

## Safety notes

- Agentic trading involves significant risk, including possible loss of principal.
- AI agents can misinterpret instructions or act on incomplete data.
- Robinhood does not control or audit third-party AI agents.
- Prefer small funded balances and review activity in the app regularly.
- Full disclosures: [Robinhood newsroom](https://robinhood.com/us/en/newsroom/robinhood-is-now-open-to-agents/) and support docs above.

## Repo layout

```
.grok/config.toml   # Project-scoped MCP server definition
README.md           # This file
```

## Links

- [Agentic Trading product page](https://robinhood.com/us/en/agentic-trading/)
- [Connect your AI agent](https://robinhood.com/us/en/support/articles/agentic-trading-overview/#ConnectyourAIagent)
- [Trading with your agent](https://robinhood.com/us/en/support/articles/trading-with-your-agent/)
- [MCP docs (Grok TUI)](https://docs.x.ai/) — local: `~/.grok/docs/user-guide/07-mcp-servers.md`
