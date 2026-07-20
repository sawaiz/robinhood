/* global document, fetch, setInterval */

const $ = (sel) => document.querySelector(sel);
const money = (n, d = 2) =>
  n == null || Number.isNaN(n)
    ? "—"
    : Number(n).toLocaleString(undefined, {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: d,
      });
const pct = (n) => (n == null || Number.isNaN(n) ? "—" : `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`);

function setText(id, text) {
  const el = $(id);
  if (el) el.textContent = text;
}

function renderMessages(messages) {
  const box = $("#messages");
  if (!messages.length) {
    box.innerHTML =
      '<div class="empty">Ask about Plan 1, levels, cash, or next steps. Replies stay in this portal.</div>';
    return;
  }
  box.innerHTML = "";
  for (const m of messages) {
    const div = document.createElement("div");
    div.className = `msg ${m.role}`;
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `${m.role}${m.mode ? " · " + m.mode : ""} · ${
      m.ts ? new Date(m.ts).toLocaleTimeString() : ""
    }`;
    const body = document.createElement("div");
    body.textContent = m.content;
    // light markdown-ish: **bold**
    body.innerHTML = escapeHtml(m.content)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\n/g, "<br/>");
    div.appendChild(meta);
    div.appendChild(body);
    box.appendChild(div);
  }
  box.scrollTop = box.scrollHeight;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

async function loadHealth() {
  try {
    const r = await fetch("/api/health");
    const h = await r.json();
    const badge = $("#badge-health");
    badge.textContent = "online";
    badge.className = "badge ok";
    $("#badge-mode").textContent = h.grok_enabled
      ? `Grok · ${h.model || "api"}`
      : "local assistant";
    $("#badge-mode").className = h.grok_enabled ? "badge ok" : "badge warn";
    $("#badge-email").textContent = h.report_email || "email";
  } catch {
    $("#badge-health").textContent = "offline";
    $("#badge-health").className = "badge warn";
  }
}

function levelProgress(price, low, high) {
  if (price == null) return 0;
  const p = ((price - low) / (high - low)) * 100;
  return Math.max(0, Math.min(100, p));
}

async function loadStatus() {
  const r = await fetch("/api/status");
  const data = await r.json();
  const st = data.status || {};
  const plan = st.plan || {};
  const q = data.quote || {};
  const d = data.derived || {};

  const price = q.price;
  const changePct = q.change_pct;
  const change = q.change;

  setText("#m-price", money(price));
  const chEl = $("#m-change");
  if (changePct != null) {
    chEl.textContent = `${money(change)} (${pct(changePct)})`;
    chEl.className = `sub ${changePct >= 0 ? "up" : "down"}`;
  }

  const pnl = d.unrealized_pnl;
  const pnlEl = $("#m-pnl");
  pnlEl.textContent = money(pnl);
  pnlEl.className = `value ${pnl != null && pnl >= 0 ? "up" : "down"}`;
  setText("#m-value", `pos ${money(d.position_value)}`);
  setText("#m-cash", money(st.cash));
  setText("#m-acct", money(d.account_est));
  setText(
    "#m-qty",
    `${plan.quantity ?? "—"} sh · avg ${money(plan.avg_cost)}`
  );

  $("#plan-status").textContent = plan.status || "—";

  const stop = plan.stop ?? 536;
  const t1 = plan.t1 ?? 585;
  const t2 = plan.t2 ?? 620;

  if (price != null) {
    setText("#dist-stop", `${pct(((price - stop) / price) * 100)} vs stop`);
    setText("#dist-mark", money(price));
    setText("#dist-t1", `${pct(((t1 - price) / price) * 100)} to T1`);
    setText("#dist-t2", `${pct(((t2 - price) / price) * 100)} to T2`);
    $("#bar-stop").style.width = `${levelProgress(price, stop - 20, t2)}%`;
    $("#bar-mark").style.width = `${levelProgress(price, stop, t2)}%`;
    $("#bar-t1").style.width = `${levelProgress(price, stop, t1)}%`;
    $("#bar-t2").style.width = `${levelProgress(price, stop, t2)}%`;

    let action = "HOLD — between stop and T1";
    let cls = "note";
    if (price <= stop) {
      action = "STOP ZONE — sell full SMH in Robinhood app or next Task";
      cls = "note";
    } else if (price >= t1) {
      action = "T1 ZONE — take profit / sell full";
    }
    const note = $("#action-note");
    note.className = cls;
    note.textContent = action + (plan.notes ? ` · ${plan.notes}` : "");
  }

  const list = $("#task-list");
  list.innerHTML = "";
  for (const t of st.tasks || []) {
    const li = document.createElement("li");
    li.innerHTML = `<div><strong>${escapeHtml(
      t.name || ""
    )}</strong><div class="purpose">${escapeHtml(
      t.purpose || ""
    )}</div></div><div class="when">${escapeHtml(t.when || "")}</div>`;
    list.appendChild(li);
  }
}

async function loadChat() {
  const r = await fetch("/api/chat");
  const data = await r.json();
  renderMessages(data.messages || []);
}

async function sendMessage(text) {
  const input = $("#chat-input");
  const btn = $("#btn-send");
  if (!text.trim()) return;
  btn.disabled = true;
  input.disabled = true;
  try {
    // optimistic user bubble
    const hist = await (await fetch("/api/chat")).json();
    const optimistic = [
      ...(hist.messages || []),
      {
        role: "user",
        content: text.trim(),
        ts: new Date().toISOString(),
      },
    ];
    renderMessages(optimistic);

    const r = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text.trim() }),
    });
    if (!r.ok) {
      const err = await r.text();
      throw new Error(err || r.statusText);
    }
    await loadChat();
    await loadStatus();
  } catch (e) {
    renderMessages([
      {
        role: "assistant",
        content: `Error: ${e.message}`,
        ts: new Date().toISOString(),
        mode: "error",
      },
    ]);
  } finally {
    btn.disabled = false;
    input.disabled = false;
    input.value = "";
    input.focus();
  }
}

async function refreshAll() {
  await Promise.all([loadHealth(), loadStatus(), loadChat()]);
}

function wire() {
  $("#btn-refresh").addEventListener("click", () => refreshAll());
  $("#btn-clear").addEventListener("click", async () => {
    if (!confirm("Clear chat history?")) return;
    await fetch("/api/chat", { method: "DELETE" });
    await loadChat();
  });
  $("#chat-form").addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage($("#chat-input").value);
  });
  $("#chat-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage($("#chat-input").value);
    }
  });
  document.querySelectorAll("[data-prompt]").forEach((btn) => {
    btn.addEventListener("click", () => sendMessage(btn.getAttribute("data-prompt")));
  });
}

wire();
refreshAll();
setInterval(loadStatus, 30_000);
setInterval(loadHealth, 60_000);
