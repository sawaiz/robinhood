# Agentic Trading Portal (local)

Local web dashboard + chat for **Plan 1 (SMH)** and further responses from the browser.

- **URL:** http://127.0.0.1:8787  
- **Quotes:** Yahoo Finance (read-only)  
- **Chat:** Local Plan-1 assistant by default; full Grok if `XAI_API_KEY` is set  
- **Queue:** Website messages also land in `data/message_queue.json` for a Grok TUI session  

This portal **does not place Robinhood orders**. Trades stay on the Robinhood app or Grok MCP Tasks.

## Quick start

```bash
cd portal
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: add XAI_API_KEY for Grok chat
python app.py
```

Open **http://127.0.0.1:8787**

Or from repo root:

```bash
./portal/run.sh
```

## Features

| Feature | Description |
|---|---|
| Dashboard | Live SMH mark, P&amp;L, cash, stop/T1/T2 distances |
| Task list | Scheduled Grok Tasks (10 / 12 / 15 ET, earnings, Friday) |
| Chat | Ask status / levels / cash / sell guidance; ongoing conversation |
| Quick actions | Buttons for common prompts |
| Message queue | `POST /api/chat` appends to `data/message_queue.json` |
| Status patch | `PATCH /api/status` to mark flat / update cash after fills |

## Optional Grok API chat

1. Get a key at [console.x.ai](https://console.x.ai)  
2. Put it in `portal/.env`:

```env
XAI_API_KEY=xai-...
XAI_MODEL=grok-3-mini
REPORT_EMAIL=sawaiz@sawaizsyed.com
```

Without a key, the portal still answers Plan 1 questions with the built-in local assistant.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Online + Grok enabled |
| GET | `/api/status` | Plan snapshot + live quote |
| PATCH | `/api/status` | Update cash / qty / plan status |
| GET | `/api/quote/{symbol}` | Live quote |
| GET/POST/DELETE | `/api/chat` | History / send / clear |
| GET/POST | `/api/queue` | Portal → TUI message bridge |

## Security

- Binds to **127.0.0.1** by default (not public internet).  
- Do not commit `.env` or chat logs.  
- No broker credentials in this app.

## Related

- Repo runbook: [../README.md](../README.md)  
- Agent rules: [../AGENTS.md](../AGENTS.md)  
