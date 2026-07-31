# Plan 6 — XLE energy equity

**Status:** **Active** (filled 2026-07-31)  
**Account:** Agentic `748082393`

## Why

Book is ~**$37** after Plan 5 options loss. Rebuild with **equity**, not OTM options.

- **XLE** = diversified energy (XOM/CVX heavy)
- Size **$32** notional · leave ~**$5** cash
- Defined % levels; fractional stops need manual/agent checks (no Grok Tasks)

## Order (executed)

| Field | Value |
|---|---|
| Side | Buy |
| Type | Market · dollar **$32.00** · GFD · regular hours |
| Symbol | XLE |
| Qty | **0.543774** |
| Avg fill | **$58.8479** (app avg ~$58.85) |
| Order id | `6a6cb6b4-0dd4-478e-b272-41ca7f63194d` |
| Filled | 2026-07-31T14:52:37Z |

## Levels

| Level | Price | Action |
|---|---:|---|
| Stop | **$55.50** | Sell full |
| T1 | **$62.00** | Sell full |
| T2 | **$64.00** | Stretch exit |

## Do not

- Average down without a new written plan  
- Switch to naked OTM options with remaining cash  
- Trade non-Agentic accounts  
