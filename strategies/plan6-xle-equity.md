# Plan 6 — XLE energy equity

**Status:** Ready · **not filled** (investor profile required)  
**Account:** Agentic `748082393`

## Why

Book is ~**$37** after Plan 5 options loss. Rebuild with **equity**, not OTM options.

- **XLE** = diversified energy (XOM/CVX heavy)
- Size **$32** notional · leave ~**$5** cash
- Defined % levels; fractional stops need manual/agent checks (no Grok Tasks)

## Order (when profile complete)

| Field | Value |
|---|---|
| Side | Buy |
| Type | Market · dollar **$32.00** · GFD · regular hours |
| Symbol | XLE |
| Spot at design | ~$58.84 (2026-07-31) |

## Levels

| Level | Price | Action |
|---|---:|---|
| Stop | **$55.50** | Sell full |
| T1 | **$62.00** | Sell full |
| T2 | **$64.00** | Stretch exit |

## Blocker

```
https://applink.robinhood.com/investment_profile?account_number=748082393&context=second_trade
```

After complete: `review_equity_order` → `place_equity_order` with same params.

## Do not

- Average down without a new written plan  
- Switch to naked OTM options with remaining cash  
- Trade non-Agentic accounts  
