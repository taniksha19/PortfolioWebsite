import { useCallback, useEffect, useRef, useState } from "react";
import { AGENT_URL } from "../../data";

// Server status: checking → ready | waking (free-tier cold start) → ready | offline
function useHealth() {
  const [health, setHealth] = useState({ status: "checking" });

  useEffect(() => {
    let cancelled = false;
    const started = Date.now();

    async function ping() {
      try {
        const res = await fetch(`${AGENT_URL}/api/health`, { signal: AbortSignal.timeout(8000) });
        if (!res.ok) throw new Error(res.statusText);
        const info = await res.json();
        if (!cancelled) setHealth({ status: "ready", ...info });
      } catch {
        if (cancelled) return;
        // Render's free tier sleeps when idle and takes up to a minute to wake.
        if (Date.now() - started < 90_000) {
          setHealth({ status: "waking" });
          setTimeout(ping, 4000);
        } else {
          setHealth({ status: "offline" });
        }
      }
    }

    ping();
    return () => {
      cancelled = true;
    };
  }, []);

  return health;
}

function toHistory(messages) {
  return messages
    .filter((m) => m.kind !== "error")
    .map((m) => ({
      role: m.role,
      content: (m.text || m.summary || (m.kind === "email" ? "Drafted an email to Taniksha." : "")).slice(0, 2000),
    }))
    .filter((m) => m.content)
    .slice(-6);
}

export function useAgent() {
  const health = useHealth();
  const [messages, setMessages] = useState([]);
  const [nodes, setNodes] = useState({}); // node name → "active" | "done"
  const [trace, setTrace] = useState([]);
  const [run, setRun] = useState({ state: "idle" }); // idle | running | finished
  const messagesRef = useRef(messages);
  messagesRef.current = messages;

  const updateLast = (fn) => setMessages((m) => [...m.slice(0, -1), fn(m[m.length - 1])]);

  const send = useCallback(
    async (text) => {
      const message = text.trim();
      if (!message || run.state === "running") return;

      const history = toHistory(messagesRef.current);
      setMessages((m) => [...m, { role: "user", text: message }, { role: "assistant", kind: "answer", text: "", streaming: true }]);
      setNodes({});
      setTrace([]);
      setRun({ state: "running" });

      const handle = (e) => {
        if (e.type === "node_start") setNodes((n) => ({ ...n, [e.node]: "active" }));
        else if (e.type === "node_end") {
          setNodes((n) => ({ ...n, [e.node]: "done" }));
          setTrace((t) => [...t, e]);
        } else if (e.type === "token") updateLast((m) => ({ ...m, text: m.text + e.text }));
        else if (e.type === "result") updateLast(() => ({ role: "assistant", ...e }));
        else if (e.type === "error") updateLast(() => ({ role: "assistant", kind: "error", text: e.message }));
        else if (e.type === "done") setRun({ state: "finished", ms: e.ms });
      };

      try {
        const res = await fetch(`${AGENT_URL}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message, history }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          const detail = typeof body.detail === "string" ? body.detail : "That message couldn't be processed.";
          throw new Error(detail);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        for (;;) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop();
          for (const part of parts) {
            if (part.startsWith("data: ")) handle(JSON.parse(part.slice(6)));
          }
        }
      } catch (err) {
        const text =
          err instanceof TypeError
            ? "Couldn't reach the agent server. It may be waking up; try again in a moment."
            : err.message;
        updateLast(() => ({ role: "assistant", kind: "error", text }));
      } finally {
        setRun((r) => (r.state === "running" ? { state: "finished" } : r));
      }
    },
    [run.state]
  );

  const reset = () => {
    setMessages([]);
    setNodes({});
    setTrace([]);
    setRun({ state: "idle" });
  };

  return { health, messages, nodes, trace, run, send, reset };
}
