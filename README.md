# Robinhood Agentic Trading

Short-term trades on a dedicated **Agentic** account via the [Robinhood Trading MCP](https://agent.robinhood.com/mcp/trading). Managed in Grok (no scheduled Tasks / email notifications).

**Not financial advice.** You can lose the whole book.

---

## Portfolio balance

![Agentic portfolio balance line chart](portal/static/charts/portfolio_balance.png)

| | |
|---|---:|
| Start (≈ Jul 20) | **~$100** |
| Now (cash) | **~$37.03** |
| Net | **~−$63** |

Data: [`portal/data/portfolio_history.json`](portal/data/portfolio_history.json)

---

## Trade ledger

| Plan | What | Result | Status |
|---|---|---:|---|
| **1** | SMH long ~$70 | **~+$2** @ T1 | Closed |
| — | USO Jul 31 $150c limit $1 | $0 | Cancelled (never filled) |
| **5** | TSLA Jul 31 $375c @ $0.90 → sold $0.25 | **−$65** | Closed (stop) |
| **6** | XLE long **$32** @ ~$58.85 | Open | **Active** |

---

## Plan 6 — XLE energy equity (**active**)

| Field | Value |
|---|---|
| Account | Agentic `748082393` |
| Symbol | **XLE** |
| Side | Buy market **$32** (RTH) |
| Qty | **0.543774** |
| Avg fill | **$58.8479** |
| Order id | `6a6cb6b4-0dd4-478e-b272-41ca7f63194d` |
| Cash left | ~**$5.03** |
| Stop | **$55.50** (~−5.5%) |
| T1 | **$62.00** (~+5%) |
| T2 | **$64.00** (~+9%) |

**Thesis:** Oil firm; XLE lagging → diversified energy equity (not OTM options).

Quote at fill (compliance):  
`Bid $58.84 × 8300 Q · Ask $58.85 × 3700 Q · Last $58.8499 × 509 D. Updated 10:52 AM ET.`

No Tasks — ask for a check or exit. Runbook: [`strategies/plan6-xle-equity.md`](strategies/plan6-xle-equity.md)

---

## Closed plans (short)

### Plan 1 — SMH (closed +)
- Buy ~0.123 sh @ ~$568 · sell ~$585 T1 · **~+$2**

### Plan 5 — TSLA $375c (closed −)
- Long 1× Jul 31 2026 **$375 call** @ **$0.90** → exit **$0.25** · **−$65**
- Details: [`strategies/plan5-tsla-bounce.md`](strategies/plan5-tsla-bounce.md)

---

## Setup

1. `/mcps` → **robinhood-trading** → `i` (OAuth)
2. Agentic only
3. No Grok Tasks / email automations

MCP: `https://agent.robinhood.com/mcp/trading`

---

## Portal

```bash
cd portal && ./run.sh   # http://127.0.0.1:8787
```

---

## Rules

| Do | Don’t |
|---|---|
| Trade **Agentic only** | Invent balances / fills |
| Prefer equity on tiny book | Blind OTM options |
| Ask agent to check / exit | Rely on Tasks or email |

---

## Repo

```
README.md
AGENTS.md
strategies/plan5-tsla-bounce.md
strategies/plan6-xle-equity.md
portal/data/status.json
portal/data/portfolio_history.json
portal/static/charts/portfolio_balance.png
```
