# Robinhood Agentic Trading

Integration with [Robinhood Agentic Trading](https://robinhood.com/us/en/agentic-trading/) via the official **Robinhood Trading MCP** server, plus an operational runbook for Grok-managed short-term plans, scheduled checks, and email reports.

Announced by [@RobinhoodApp](https://x.com/RobinhoodApp): *“Robinhood is now open to AI agents.”* Connect an AI agent through Model Context Protocol (MCP), open a dedicated Agentic account, and let the agent research, trade equities/options, and manage a portfolio on your behalf.

**Not financial advice.** Markets can go to zero. Only fund money you can afford to lose.

---

## Table of contents

1. [MCP endpoint](#mcp-endpoint)
2. [Setup (Grok Build TUI)](#setup-grok-build-tui)
3. [Account rules](#account-rules)
4. [Process history](#process-history)
5. [Plan 1 — SMH semi pullback (active)](#plan-1--smh-semi-pullback-active)
6. [Signal board (how ideas are sourced)](#signal-board-how-ideas-are-sourced)
7. [Scheduled tasks & email reports](#scheduled-tasks--email-reports)
8. [Manual checklist](#manual-checklist)
9. [Other platforms](#other-platforms)
10. [Safety notes](#safety-notes)
11. [Repo layout](#repo-layout)
12. [Links](#links)

---

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

OAuth discovery (for debugging auth):

| Field | Value |
|---|---|
| Authorization | `https://robinhood.com/oauth` |
| Token | `https://api.robinhood.com/oauth2/token/` |
| Registration | `https://agent.robinhood.com/oauth/trading/register` |

---

## Setup (Grok Build TUI)

This repo includes project-scoped MCP config at [`.grok/config.toml`](.grok/config.toml). The same server may also be registered in user config (`~/.grok/config.toml`).

### 1. Authenticate (OAuth)

Robinhood’s MCP requires OAuth. From a Grok session in this directory:

1. Run `/mcps` (or open MCP Servers via the plugins panel).
2. Select **robinhood-trading**.
3. Press **`i`** to authenticate — Grok opens a browser OAuth flow.
4. Sign in with your Robinhood account and complete Agentic account onboarding **on desktop** (required by Robinhood).

Verify connectivity:

```bash
grok mcp doctor robinhood-trading
```

After auth succeeds, doctor should report the server as healthy. Tokens are stored locally under `~/.grok/mcp_credentials.json` (owner-only permissions). **Do not commit credentials.**

### 2. Open & fund an Agentic account

During MCP authentication Robinhood prompts you to open a dedicated **Agentic** account. Fund only what you want the agent to trade with.

| Capability | Scope |
|---|---|
| Read | Balances, positions, orders, watchlists (broader account visibility) |
| Write / trade | **Agentic account only** |
| Notifications | Robinhood push on trades; app P&amp;L |
| Disconnect | Anytime in the Robinhood app |

### 3. Use tools from Grok

1. Discover tools: `search_tool` with query `"robinhood"` or `"trading"`.
2. Call tools: `use_tool` with qualified name `robinhood-trading__<tool>`.
3. Prefer read-only analysis unless you explicitly ask to place/cancel orders.

Example prompts:

- “What’s my Agentic buying power and positions?”
- “Plan 1 check — act if stop or T1 hit.”
- “Manage Plan 1 SMH vs $536 / $585 / $620.”

---

## Account rules

| Rule | Detail |
|---|---|
| Trade only | **Agentic** account (`agentic_allowed=true`) |
| Never invent | Balances, fills, or P&amp;L — always pull live MCP data |
| Confirm | Large or ambiguous orders; summarize symbol, side, size, type first |
| Options | Require options level on the agentic account; multi-leg not via MCP yet |
| Fractional limits | Dollar/fractional buys are **market + regular hours** only; **stop orders fail on fractional** |

Agent rules for this repo live in [AGENTS.md](AGENTS.md).

---

## Process history

| When (UTC) | Event |
|---|---|
| 2026-07-20 | Repo initialized; Robinhood Trading MCP configured |
| 2026-07-20 | OAuth connected; Agentic account funded (**$100** cash) |
| 2026-07-20 | Research: X + Truth Social themes; live quotes; earnings calendar |
| 2026-07-20 | **Plan 1 executed**: buy **SMH** $70 market on Agentic |
| 2026-07-20 | Fractional stop at $536 **rejected** by broker API |
| 2026-07-20 | Grok **Tasks** scheduled for manage + email reports |

There was **no prior trade history** on the Agentic book before Plan 1.

---

## Plan 1 — SMH semi pullback (active)

### Thesis

Late-week semiconductor washout + AI/compute demand narrative → mean-reversion bounce in the semi complex. **SMH** (VanEck Semiconductor ETF) used as diversified vehicle (vs single-name MU/SNDK chase after large green opens).

### Entry (executed)

| Field | Value |
|---|---|
| Account | Agentic (self-directed cash) |
| Symbol | **SMH** |
| Side | Buy |
| Type | Market · GFD · regular hours |
| Notional | **$70.00** |
| Quantity | **0.123224** shares |
| Avg fill | **$568.0699** |
| Fees | $0 |
| Order id | `6a5e499f-a510-43ca-be9c-8d444d3718ad` |
| Placed by | agentic (MCP) |
| Cash remaining | **~$30** |

**Note:** Ideal written entry zone was a pullback to **$555–562**. Live price was ~**$568**; fractional SMH cannot rest a limit, so execution used a **market dollar** order.

### Management levels

| Level | Price | Action |
|---|---:|---|
| **Hard stop** | **$536** | Sell full position (manual or scheduled task) |
| **T1** | **$585–600** | Sell all (or half if you override) |
| **T2** | **$620** | Stretch exit if complex holds |
| **Invalidation** | Daily close under Fri lows + QQQ breakdown | Exit thesis |

Approximate risk from fill ~$568 → stop $536: about **−5.6%** on the position (~**−$4** on $70).

### Why no resting stop

Robinhood MCP rejected fractional SMH stop-market orders (`Invalid trigger for fractional order` / invalid TIF). **Stops are enforced by scheduled Tasks + manual app alerts**, not a GTC stop on the book.

### Horizon

- Target hold: **2–10 trading days**
- Reassess if still under **~$575** by end of the week with no progress

### Do not (unless new plan)

- Chase **MU / SNDK** after large single-day rips with residual cash
- Deploy last **$30** without a defined second-tranche rule
- Trade non-Agentic accounts via the agent

---

## Signal board (how ideas are sourced)

Plans are ranked from **social + live market + calendar**, not tip spam.

### Themes used (Jul 2026 week)

| Theme | Sources | Vehicles | Reliability note |
|---|---|---|---|
| Semi / memory bounce | X (SMH, MU, SNDK, NVDA, AMD) | SMH, NVDA, MU | Highest consensus; avoid FOMO after +5–7% days |
| Energy / Hormuz | X + macro; Truth Social de-escalation risk | XLE, USO, XOM | Two-sided; peace headlines crush oil |
| Mega earnings | Robinhood earnings calendar | GOOGL, TSLA, INTC, META, MSFT, AAPL | Prefer reaction over overnight binary on small accounts |
| Truth Social | News/history, not a live API | Index / oil / name spikes | Retail is late; use as **headline risk**, not tips |

### Live tape helpers

| Signal | Bullish for Plan 1 | Bearish |
|---|---|---|
| SMH vs QQQ | SMH leads | SMH lagging hard |
| UVXY | Falling | Spike (risk-off) |
| IWM | Catch-up green | Diverges lower |
| AAPL vs QQQ | Weak AAPL + strong semis = rotation OK | Broad mega-cap dump |

### Other plan sketches (not active)

Documented for context only — **do not auto-trade** unless explicitly armed:

| Plan | Idea | Status |
|---|---|---|
| 2 | MU pullback satellite | Not armed |
| 3 | GOOGL earnings reaction | Watch only |
| 4 | TSLA earnings reaction | Watch only |
| 5 | Energy / Hormuz | Watch only |
| 6 | INTC earnings | Watch only |
| 8 | BABA satellite | Not armed |
| 9 | Cash / do nothing | Valid default |

---

## Scheduled tasks & email reports

Grok **Tasks** MCP jobs run on a cadence, execute Plan 1 management prompts, and notify via **email + app**. Report content is addressed to:

**sawaiz@sawaizsyed.com**

> Delivery uses the notification email on the **Grok / xAI account**. Ensure that account receives mail at (or forwards to) `sawaiz@sawaizsyed.com`.

### Active tasks

| Name | Cadence (America/New_York) | Purpose |
|---|---|---|
| `plan1-smh-daily-10et` | Weekdays **10:00** | Full status; auto-sell on stop/T1/T2 |
| `plan1-smh-midday-12et` | Weekdays **12:00** | Level watch |
| `plan1-smh-powerhour-15et` | Weekdays **15:00** | Level watch + overnight risk note |
| `plan1-earnings-wed-722` | **2026-07-22 10:00** (one-shot) | Pre GOOGL/TSLA |
| `plan1-post-earnings-thu-723` | **2026-07-23 10:00** (one-shot) | Post-earnings gap manage |
| `plan1-weekly-fri-review` | **Fridays 10:00** | Weekly P&amp;L + keep/kill thesis |

### Auto-actions on each run

1. Load Agentic portfolio + SMH position (live MCP only).
2. If SMH **≤ $536** or **≥ $585** (or **≥ $620**): **sell full position** market RTH.
3. Else **hold** and email a short status (price, qty, P&amp;L, distance to levels).
4. Never trade non-Agentic accounts.

### Cadence limits

| Wanted | Reality |
|---|---|
| True price webhooks | **Not** available via Robinhood MCP |
| Hourly Tasks RRULE | **Not** supported (daily/weekly/monthly/yearly only) |
| Level coverage | **3× per weekday** (10 / 12 / 15 ET) |
| Instant stop | Use **Robinhood app price alerts** at $536 and $585 |

### Managing tasks

In a Grok session with Tasks MCP enabled:

- List: `tasks__list`
- Pause: `tasks__pause` with `is_enabled: false`
- Delete/archive: `tasks__delete`
- Results: `tasks__get_results`

Or ask: *“pause Plan 1 tasks”* / *“delete Plan 1 schedules”*.

### Recommended Robinhood app alerts

| Alert | Level |
|---|---:|
| SMH below | **536** |
| SMH above | **585** |
| Optional stretch | **620** |

---

## Manual checklist

### Between automated runs

- [ ] If SMH **&lt; $536** in the app → sell full position (don’t wait for next task).
- [ ] If SMH **≥ $585** → take T1 (or confirm task sold).
- [ ] Ignore noise unless UVXY spikes hard or major Hormuz/Truth Social macro headline.

### Session prompts (copy-paste)

```text
Plan 1 check — act if stop or T1 hit. Email summary to sawaiz@sawaizsyed.com.
```

```text
Manage Plan 1 SMH: check vs stop 536 and targets 585/620; sell if rules hit; otherwise hold. Report P&L only.
```

### After flat

1. Pause or archive Plan 1 tasks.
2. Journal outcome (entry, exit, reason).
3. Only arm a new plan with explicit user request.

---

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

Scheduled Tasks + email in this runbook are **Grok-specific**.

---

## Safety notes

- Agentic trading involves significant risk, including possible loss of principal.
- AI agents can misinterpret instructions or act on incomplete data.
- Robinhood does not control or audit third-party AI agents.
- Prefer small funded balances and review activity in the app regularly.
- Social media (X, Truth Social) is **not** a reliable alpha source; treat as narrative/risk context.
- Automated sells can miss gaps or print through levels; app alerts are mandatory for hard stops.
- Full disclosures: [Robinhood newsroom](https://robinhood.com/us/en/newsroom/robinhood-is-now-open-to-agents/) and support docs below.

---

## Repo layout

```
.grok/config.toml   # Project-scoped MCP server definition
AGENTS.md           # Agent safety / MCP usage rules
README.md           # This runbook
.gitignore          # Ignores secrets / env files
```

**Never commit:** OAuth tokens, `mcp_credentials.json`, API keys, `.env`, or full account numbers.

---

## Links

- [Agentic Trading product page](https://robinhood.com/us/en/agentic-trading/)
- [Connect your AI agent](https://robinhood.com/us/en/support/articles/agentic-trading-overview/#ConnectyourAIagent)
- [Trading with your agent](https://robinhood.com/us/en/support/articles/trading-with-your-agent/)
- [Agentic Trading overview](https://robinhood.com/us/en/support/articles/agentic-trading-overview/)
- [MCP docs (Grok TUI)](https://docs.x.ai/) — local: `~/.grok/docs/user-guide/07-mcp-servers.md`
- Background tasks /loops: `~/.grok/docs/user-guide/20-background-tasks.md`
