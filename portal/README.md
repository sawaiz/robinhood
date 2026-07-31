# Agentic portal

```bash
cd portal && ./run.sh
# http://127.0.0.1:8787
```

- **Top:** portfolio balance chart (`static/charts/portfolio_balance.png`)
- Status from `data/status.json` + Yahoo quote for plan symbol
- Chat: local assistant or Grok if `XAI_API_KEY` in `.env`

Does **not** place orders.