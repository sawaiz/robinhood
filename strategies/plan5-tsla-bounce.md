# Plan 5 — TSLA Dip Bounce Starter

**Status:** Active (filled)  
**Account:** Agentic `748082393` only  
**Not financial advice.** Options can go to zero.

## Thesis

TSLA dumped hard (~−12% vs prior close ~$374 → spot ~$328 on 2026-07-23). Plan 5 is a **defined-risk bounce starter**: long 1 short-dated OTM call to capture a relief bounce / mean-reversion into prior-day levels, with mechanical **save levels** (take-profit / stop) so the ~$100 book is not held blind into expiry.

Why not ATM or shares:

- 1 TSLA share ≈ $328 (too large / no leverage for this book).
- Nearer strikes (340–360) cost $180–$535 — over buying power.
- $375c is the closest liquid strike that still fits ≤ $100 debit with a tight market.

## Position (live)

| Field | Value |
|---|---|
| Strategy | Long call (Level 2) |
| Underlying | TSLA |
| Contract | **Jul 31 2026 $375 Call** |
| Option ID | `53c52a9d-bdb7-42c2-88eb-b46976caf14b` |
| Qty | 1 |
| Order ID | `6a621de6-3d96-46f6-ab57-1b99d497c532` |
| Fill | **$0.90** (limit was $0.91) |
| Debit | **$90.00** (+ ~$0.04 fees) |
| Multiplier | 100 |
| Expiry / sellout | 2026-07-31 · sellout ~19:30 UTC |
| Spot at entry | ~$327.91 |
| Break-even @ expiry | **$375.90** |
| Approx. need | TSLA ≳ **+14.6%** by expiry for intrinsic profit |

## Save ladder (premium-based)

All targets use **option mark / mid**, not only stock price. With 1 contract, T1/T2 are **full closes** (no scale-out).

| Level | Premium | P&L vs $0.90 | Action |
|---|---:|---:|---|
| **Stop** | **$0.45** | **−$45 (−50%)** | Sell-to-close immediately |
| **Entry** | $0.90 | $0 | — |
| **T1 save** | **$1.40** | **+$50 (~+56%)** | Sell-to-close (bank the bounce) |
| **T2 save** | **$1.85** | **+$95 (~+106%)** | If still open and ripping, close here (runner target) |

### Stock-side invalidation (optional hard stop)

- If TSLA last trade **&lt; $310** on a sustained basis during RTH and premium has not already hit stop → prefer exit (structure broke).
- Do **not** average down. No second contract unless cash remains and thesis re-validates after a fresh review.

### Time stop

- If neither T1 nor stop hit by **2026-07-30 15:00 ET**, sell-to-close before last full session into expiry (avoid pin/gamma day).

## Expected outcomes (mechanical, expiry)

| TSLA @ expiry | Intrinsic | P&L |
|---:|---:|---:|
| ≤ $375 | $0 | **−$90 (−100%)** |
| $376 | $100 | +$10 |
| $380 | $500 | +$410 |
| $400 | $2,500 | +$2,410 |

**Path matter:** most realistic wins are **mid-path premium spikes** on a bounce (T1/T2), not expiry ITM.

## Risk

- Max loss ≈ **$90** (premium) + fees.
- IV already elevated post-dump; vol crush on bounce can limit premium gains even if stock rises modestly.
- Model chance_of_profit_long at entry was ~**6%** (expiry ITM/BE) — this is a **starter lottery with rules**, not a high-probability income trade.
- Agentic only; no multi-leg hedges via MCP.

## Monitoring

Grok Tasks (email `sawaiz@sawaizsyed.com` when configured):

1. Open / 10:00 ET — quote + save check + auto-exit if stop/T1/T2/time
2. Midday 12:00 ET — same
3. Power hour 15:00 ET — same + overnight note

Portal: `portal/data/status.json` plan id `plan5`.  
Chart: `portal/static/charts/plan5_tsla_bounce.png`.

## Exit checklist (agent)

1. `get_option_quotes` on option_id.
2. If mark ≤ stop **or** mark ≥ T1 (prefer T1 first if both somehow true) → `review_option_order` sell-to-close then `place_option_order`.
3. If mark ≥ T2 and still open → close.
4. If date ≥ 2026-07-30 15:00 ET ET and still open → close.
5. Update `portal/data/status.json` and this file status.

## Do not

- Hold through 7/31 hoping for a miracle pin without a bounce signal.
- Roll without a new written plan.
- Trade non-Agentic accounts.
