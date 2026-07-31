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

Plan 6 (XLE energy equity) — primary:
- Account: Agentic only · cash ~${cash}
- Intended: buy market $32 XLE · stop $55.50 · T1 $62 · T2 $64
- Status may be ready_blocked_profile until investor profile is done
- Prior: Plan 1 SMH closed +$2; Plan 5 TSLA 375c closed -$65
- Never invent fills; use live quotes when provided

Be concise, practical, not financial advice.
""".strip()


def local_assistant(user_text: str, status: Dict[str, Any], quote: Optional[Dict[str, Any]]) -> str:
    plan = status.get("plan") or {}
    cash = float(status.get("cash") or 0)
    qty = plan.get("quantity") or 0
    avg = float(plan.get("avg_cost") or 0)
    stop = float(plan.get("stop") or 55.5)
    t1 = float(plan.get("t1") or 62)
    t2 = float(plan.get("t2") or 64)
    sym = plan.get("symbol") or "XLE"
    price = quote.get("price") if quote else None
    text = user_text.lower().strip()
    blocker = status.get("blocker") or {}

    def pnl_block() -> str:
        total = float(status.get("total_value") or cash)
        lines = [
            f"**Account** ~${total:.2f} cash ${cash:.2f}",
            f"**{plan.get('id', 'plan').upper()}** {plan.get('name', '')} · status `{plan.get('status')}`",
            f"Symbol **{sym}** · stop ${stop:.2f} · T1 ${t1:.2f} · T2 ${t2:.2f}",
        ]
        if price is not None:
            lines.append(f"Live {sym} ${float(price):.2f}")
        if qty and avg and price is not None:
            value = float(qty) * float(price)
            cost = float(qty) * avg
            pnl = value - cost
            lines.append(f"Position ~${value:.2f} · P&L ${pnl:+.2f}")
        elif plan.get("dollar_amount"):
            lines.append(f"Not filled yet · intended buy ${plan.get('dollar_amount')}")
        if blocker.get("url"):
            lines.append(f"Blocker: {blocker.get('message')} → {blocker.get('url')}")
        lines.append("**Not financial advice.**")
        return "\n".join(lines)

    if any(k in text for k in ("status", "pnl", "p&l", "position", "how am i", "check plan", "plan 6", "plan6", "balance")):
        return pnl_block()

    if any(k in text for k in ("remaining", "cash", "leftover", "rest of")):
        return (
            f"**${cash:.2f} cash** on Agentic (~$37 after Plan 5).\n"
            f"Plan 6: deploy **$32** to XLE after investor profile; keep ~$5 buffer.\n\n"
            + pnl_block()
        )

    if any(k in text for k in ("stop", "level", "target", "t1", "t2")):
        return (
            f"Plan 6 levels ({sym}):\n"
            f"- **Stop** ${stop:.2f} → sell full\n"
            f"- **T1** ${t1:.2f} → sell full\n"
            f"- **T2** ${t2:.2f} stretch\n\n"
            + pnl_block()
        )

    if any(k in text for k in ("sell", "exit", "close position")):
        return (
            f"Portal cannot place broker orders. Sell {sym} in the **Robinhood app** "
            "or ask Grok MCP to sell-to-close on Agentic."
        )

    if any(k in text for k in ("profile", "block", "execute", "buy")):
        url = blocker.get("url") or (
            "https://applink.robinhood.com/investment_profile"
            "?account_number=748082393&context=second_trade"
        )
        return (
            "Plan 6 is **ready but blocked** until the investor profile is complete.\n"
            f"Link: {url}\n"
            "Then say **execute Plan 6** in Grok TUI."
        )

    if text in ("help", "?", "hi", "hello"):
        return (
            "Try: **status** · **levels** · **cash** · **plan6** · **help**\n\n"
            + pnl_block()
        )

    return pnl_block() + "\n\nAsk: status · levels · cash · plan6 · help"


async def grok_chat(messages: List[Dict[str, str]], status: Dict[str, Any], quote: Optional[Dict[str, Any]]) -> str:
    plan = status.get("plan") or {}
    sys = SYSTEM_CONTEXT.format(
        email=status.get("report_email", REPORT_EMAIL),
        cash=status.get("cash"),
    )
    if quote:
        sys += f"\n\nLive quote: {json.dumps(quote)}"
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
    cash = float(status.get("cash") or 0)
    account_est = float(status.get("total_value") or cash)
    if mark is not None:
        account_est = mark + cash
    return {
        "status": status,
        "quote": quote,
        "derived": {
            "position_value": mark,
            "unrealized_pnl": pnl,
            "account_est": account_est,
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
