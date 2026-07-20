"""
Local Robinhood Agentic Trading portal.

Dashboard + chat. Live quotes via Yahoo. Chat uses xAI Grok when XAI_API_KEY
is set; otherwise a local Plan-1-aware assistant answers.
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
STATIC = ROOT / "static"
STATUS_PATH = DATA / "status.json"
CHAT_PATH = DATA / "chat_history.json"
QUEUE_PATH = DATA / "message_queue.json"

load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

REPORT_EMAIL = os.getenv("REPORT_EMAIL", "sawaiz@sawaizsyed.com")
XAI_API_KEY = os.getenv("XAI_API_KEY") or os.getenv("GROK_CODE_XAI_API_KEY")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-3-mini")
XAI_BASE = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")

app = FastAPI(title="Robinhood Agentic Portal", version="1.0.0")


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_status() -> Dict[str, Any]:
    st = _read_json(STATUS_PATH, {})
    st.setdefault("report_email", REPORT_EMAIL)
    return st


def load_chat() -> List[Dict[str, Any]]:
    return _read_json(CHAT_PATH, [])


def save_chat(messages: List[Dict[str, Any]]) -> None:
    # keep last 200
    _write_json(CHAT_PATH, messages[-200:])


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------

async def fetch_quote(symbol: str) -> Dict[str, Any]:
    symbol = symbol.upper().strip()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"interval": "1m", "range": "1d"}
    headers = {"User-Agent": "Mozilla/5.0 (RobinhoodPortal/1.0)"}
    async with httpx.AsyncClient(timeout=12.0) as client:
        r = await client.get(url, params=params, headers=headers)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Quote provider error {r.status_code}")
        body = r.json()
    try:
        result = body["chart"]["result"][0]
        meta = result["meta"]
        price = meta.get("regularMarketPrice") or meta.get("previousClose")
        prev = meta.get("chartPreviousClose") or meta.get("previousClose")
        currency = meta.get("currency", "USD")
        name = meta.get("longName") or meta.get("shortName") or symbol
        change = None
        change_pct = None
        if price is not None and prev:
            change = float(price) - float(prev)
            change_pct = (change / float(prev)) * 100.0
        return {
            "symbol": symbol,
            "name": name,
            "price": float(price) if price is not None else None,
            "previous_close": float(prev) if prev is not None else None,
            "change": change,
            "change_pct": change_pct,
            "currency": currency,
            "as_of": datetime.now(timezone.utc).isoformat(),
            "source": "yahoo",
        }
    except (KeyError, IndexError, TypeError, ValueError) as e:
        raise HTTPException(status_code=502, detail=f"Could not parse quote: {e}") from e


# ---------------------------------------------------------------------------
# Local Plan-1 assistant (no API key required)
# ---------------------------------------------------------------------------

SYSTEM_CONTEXT = """
You are the local assistant for a Robinhood Agentic Trading portal.
User report email: {email}

Active Plan 1 (SMH semi pullback):
- Account: Agentic only
- Long SMH, qty ~{qty}, avg ~${avg}
- Stop $536 → sell full; T1 $585 → sell full; T2 $620 stretch
- Cash remaining ~${cash} — leave as cash unless SMH dips to $555–562 for optional add
- Fractional stops unsupported; Grok Tasks check 10/12/15 ET weekdays
- Never invent fills; prefer live quotes when provided

Be concise, practical, not financial advice.
""".strip()


def local_assistant(user_text: str, status: Dict[str, Any], quote: Optional[Dict[str, Any]]) -> str:
    plan = status.get("plan") or {}
    cash = status.get("cash", 30)
    qty = plan.get("quantity", 0)
    avg = plan.get("avg_cost", 0)
    stop = float(plan.get("stop", 536))
    t1 = float(plan.get("t1", 585))
    t2 = float(plan.get("t2", 620))
    price = quote.get("price") if quote else None
    text = user_text.lower().strip()

    def pnl_block() -> str:
        if price is None or not qty:
            return "No live mark available."
        value = float(qty) * float(price)
        cost = float(qty) * float(avg)
        pnl = value - cost
        pct = (pnl / cost * 100) if cost else 0
        dist_stop = ((float(price) - stop) / float(price)) * 100
        dist_t1 = ((t1 - float(price)) / float(price)) * 100
        action = "HOLD"
        if float(price) <= stop:
            action = "STOP HIT → sell full SMH (manual or wait for next Task)"
        elif float(price) >= t1:
            action = "T1 HIT → take profit / sell full"
        elif float(price) >= t2:
            action = "T2 HIT → exit stretch"
        return (
            f"**SMH** mark ${price:.2f} · qty {qty} · avg ${avg:.2f}\n"
            f"Position value ~${value:.2f} · P&L ~${pnl:+.2f} ({pct:+.2f}%)\n"
            f"Cash ${cash:.2f} · Account ~${value + float(cash):.2f}\n"
            f"Stop ${stop:.0f} ({dist_stop:+.1f}% away) · T1 ${t1:.0f} ({dist_t1:+.1f}% to go)\n"
            f"**Action: {action}**"
        )

    if any(k in text for k in ("status", "pnl", "p&l", "position", "how am i", "check plan", "plan 1")):
        return pnl_block() + "\n\n_Not financial advice. Live trading remains on Robinhood + Grok Tasks._"

    if any(k in text for k in ("remaining", "cash", "30", "rest of", "leftover")):
        return (
            f"You have **${cash:.2f} cash** left on Agentic.\n\n"
            "Recommendation: **keep it as cash**. Only deploy on an SMH dip to "
            f"**$555–562** as a small second tranche. Do not chase MU/SNDK/energy with it.\n\n"
            + pnl_block()
        )

    if any(k in text for k in ("stop", "level", "target", "t1", "t2", "536", "585")):
        return (
            f"Plan 1 levels:\n"
            f"- **Stop** ${stop:.0f} → sell full\n"
            f"- **T1** ${t1:.0f}–600 → sell full (or half if you override)\n"
            f"- **T2** ${t2:.0f} stretch\n"
            f"- Ideal add zone $555–562 (optional)\n\n"
            + (pnl_block() if price else "")
        )

    if any(k in text for k in ("sell", "exit", "close position")):
        if price is not None and float(price) <= stop:
            return (
                f"Price ${price:.2f} is at/below stop ${stop:.0f}. "
                "This portal **cannot** place Robinhood orders. "
                "Sell full SMH in the **Robinhood app**, or wait for the next Grok Task "
                "(10/12/15 ET) which is authorized to sell on Agentic. "
                "Also set app alerts at 536/585."
            )
        if price is not None and float(price) >= t1:
            return (
                f"Price ${price:.2f} is at/above T1 ${t1:.0f}. "
                "Take profit in the **Robinhood app** or let the next Task sell. "
                "This web portal does not submit broker orders."
            )
        return (
            "To exit early: sell SMH in the **Robinhood app** (full 0.123224 shares), "
            "then tell this chat “flat” so status can be updated. "
            "Portal itself cannot place broker orders — only Grok MCP Tasks / the app can."
        )

    if any(k in text for k in ("task", "schedule", "email", "when")):
        tasks = status.get("tasks") or []
        lines = [f"- **{t.get('name')}** — {t.get('when')}: {t.get('purpose')}" for t in tasks]
        return (
            f"Reports address: **{status.get('report_email', REPORT_EMAIL)}**\n\n"
            "Scheduled Tasks:\n" + "\n".join(lines) +
            "\n\nBetween runs, use Robinhood app price alerts at $536 and $585."
        )

    if any(k in text for k in ("flat", "sold", "closed", "no position")):
        status["plan"] = {**plan, "status": "closed", "quantity": 0}
        status["cash"] = float(status.get("total_value") or status.get("cash") or 100)
        status["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_json(STATUS_PATH, status)
        return "Marked Plan 1 as **closed** in portal status. Pause/archive Grok Tasks so emails stop."

    if text in ("help", "?", "hi", "hello"):
        return (
            "Local Agentic portal. Try:\n"
            "- **status** — Plan 1 P&L and action\n"
            "- **levels** — stop / T1 / T2\n"
            "- **cash** — remaining $30 guidance\n"
            "- **tasks** — schedule + email\n"
            "- **sell** — how to exit (app / Tasks)\n"
            "- Free-form questions (full Grok if `XAI_API_KEY` set)\n\n"
            + pnl_block()
        )

    # generic local reply
    return (
        "Local mode (no XAI_API_KEY). Here's Plan 1 context:\n\n"
        + pnl_block()
        + "\n\nAsk: status · levels · cash · tasks · sell · help\n"
        "Set `XAI_API_KEY` in `portal/.env` for full Grok answers from this site."
    )


async def grok_chat(messages: List[Dict[str, str]], status: Dict[str, Any], quote: Optional[Dict[str, Any]]) -> str:
    plan = status.get("plan") or {}
    sys = SYSTEM_CONTEXT.format(
        email=status.get("report_email", REPORT_EMAIL),
        qty=plan.get("quantity"),
        avg=plan.get("avg_cost"),
        cash=status.get("cash"),
    )
    if quote:
        sys += f"\n\nLive quote SMH: {json.dumps(quote)}"
    sys += f"\n\nPortal status JSON: {json.dumps(status)[:4000]}"

    payload = {
        "model": XAI_MODEL,
        "messages": [{"role": "system", "content": sys}] + messages,
        "temperature": 0.4,
    }
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.post(f"{XAI_BASE}/chat/completions", headers=headers, json=payload)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"xAI API {r.status_code}: {r.text[:400]}")
        data = r.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=502, detail=f"Bad xAI response: {e}") from e


# ---------------------------------------------------------------------------
# API models
# ---------------------------------------------------------------------------

class ChatIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    use_grok: Optional[bool] = None  # default: use Grok if key present


class StatusPatch(BaseModel):
    cash: Optional[float] = None
    quantity: Optional[float] = None
    avg_cost: Optional[float] = None
    plan_status: Optional[str] = None
    notes: Optional[str] = None


class QueueIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "grok_enabled": bool(XAI_API_KEY),
        "model": XAI_MODEL if XAI_API_KEY else None,
        "report_email": REPORT_EMAIL,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/status")
async def get_status():
    status = load_status()
    symbol = (status.get("plan") or {}).get("symbol", "SMH")
    quote = None
    try:
        quote = await fetch_quote(symbol)
    except Exception as e:
        quote = {"error": str(e), "symbol": symbol}
    plan = status.get("plan") or {}
    mark = None
    pnl = None
    if quote and quote.get("price") is not None and plan.get("quantity"):
        mark = float(plan["quantity"]) * float(quote["price"])
        cost = float(plan["quantity"]) * float(plan.get("avg_cost") or 0)
        pnl = mark - cost
    return {
        "status": status,
        "quote": quote,
        "derived": {
            "position_value": mark,
            "unrealized_pnl": pnl,
            "account_est": (mark or 0) + float(status.get("cash") or 0),
        },
    }


@app.patch("/api/status")
async def patch_status(body: StatusPatch):
    status = load_status()
    plan = status.setdefault("plan", {})
    if body.cash is not None:
        status["cash"] = body.cash
        status["buying_power"] = body.cash
    if body.quantity is not None:
        plan["quantity"] = body.quantity
    if body.avg_cost is not None:
        plan["avg_cost"] = body.avg_cost
    if body.plan_status is not None:
        plan["status"] = body.plan_status
    if body.notes is not None:
        plan["notes"] = body.notes
    status["updated_at"] = datetime.now(timezone.utc).isoformat()
    status["plan"] = plan
    _write_json(STATUS_PATH, status)
    return {"ok": True, "status": status}


@app.get("/api/quote/{symbol}")
async def quote(symbol: str):
    return await fetch_quote(symbol)


@app.get("/api/chat")
async def chat_history():
    return {"messages": load_chat(), "grok_enabled": bool(XAI_API_KEY)}


@app.post("/api/chat")
async def chat(body: ChatIn):
    status = load_status()
    plan = status.get("plan") or {}
    symbol = plan.get("symbol", "SMH")
    quote = None
    try:
        quote = await fetch_quote(symbol)
    except Exception:
        quote = None

    history = load_chat()
    user_msg = {
        "id": str(uuid.uuid4()),
        "role": "user",
        "content": body.message.strip(),
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    history.append(user_msg)

    use_grok = body.use_grok if body.use_grok is not None else bool(XAI_API_KEY)
    mode = "grok" if use_grok and XAI_API_KEY else "local"

    if mode == "grok":
        # last 20 turns for context
        api_msgs = [
            {"role": m["role"], "content": m["content"]}
            for m in history
            if m["role"] in ("user", "assistant")
        ][-20:]
        try:
            reply = await grok_chat(api_msgs, status, quote)
        except HTTPException:
            reply = local_assistant(body.message, status, quote)
            reply = f"_(Grok API failed — local fallback)_\n\n{reply}"
            mode = "local_fallback"
    else:
        reply = local_assistant(body.message, status, quote)

    asst = {
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": reply,
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
    }
    history.append(asst)
    save_chat(history)

    # also queue for external Grok TUI pick-up
    q = _read_json(QUEUE_PATH, [])
    q.append({
        "id": user_msg["id"],
        "message": body.message.strip(),
        "ts": user_msg["ts"],
        "source": "portal",
        "handled": False,
    })
    _write_json(QUEUE_PATH, q[-100:])

    return {"message": asst, "quote": quote, "mode": mode}


@app.delete("/api/chat")
async def clear_chat():
    save_chat([])
    return {"ok": True}


@app.get("/api/queue")
async def get_queue():
    """Messages from the website for a Grok TUI session to pick up."""
    return {"items": _read_json(QUEUE_PATH, [])}


@app.post("/api/queue")
async def post_queue(body: QueueIn):
    q = _read_json(QUEUE_PATH, [])
    item = {
        "id": str(uuid.uuid4()),
        "message": body.message.strip(),
        "ts": datetime.now(timezone.utc).isoformat(),
        "source": "portal",
        "handled": False,
    }
    q.append(item)
    _write_json(QUEUE_PATH, q[-100:])
    return {"ok": True, "item": item}


@app.post("/api/queue/{item_id}/handled")
async def mark_queue_handled(item_id: str):
    q = _read_json(QUEUE_PATH, [])
    for item in q:
        if item.get("id") == item_id:
            item["handled"] = True
    _write_json(QUEUE_PATH, q)
    return {"ok": True}


# Static frontend
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


def main():
    import uvicorn

    host = os.getenv("PORTAL_HOST", "127.0.0.1")
    port = int(os.getenv("PORTAL_PORT", "8787"))
    uvicorn.run("app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
