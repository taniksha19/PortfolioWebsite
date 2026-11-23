/* Nimbus talks to the real LangGraph agent (same /api/chat stream the simple site uses).
   If the server is asleep or unreachable, it falls back to short answers from the portfolio. */
const chatHistory = [];
async function askAgent(q, el) {
  let text = "";
  try {
    const res = await fetch(agentUrl + "/api/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: q, history: chatHistory.slice(-6) }), signal: AbortSignal.timeout(60000),
    });
    if (!res.ok || !res.body) throw new Error("agent unavailable");
    const reader = res.body.getReader(), dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const parts = buf.split("\n\n"); buf = parts.pop();
      for (const part of parts) {
        if (!part.startsWith("data: ")) continue;
        const e = JSON.parse(part.slice(6));
        if (e.type === "token") { text += e.text; el.classList.remove("typing"); el.textContent = text; }
        else if (e.type === "result") { const r = e.text || e.summary; if (r) { text = r; el.classList.remove("typing"); el.textContent = r; } }
        else if (e.type === "error") throw new Error(e.message);
      }
    }
    if (!text.trim()) throw new Error("empty answer");
  } catch {
    text = nimbusAnswer(q);
    el.classList.remove("typing"); el.textContent = text;
  }
  chatHistory.push({ role: "user", content: q.slice(0, 2000) }, { role: "assistant", content: text.slice(0, 2000) });
  return text;
}
