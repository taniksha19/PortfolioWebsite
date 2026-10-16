import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowCounterClockwiseIcon, ArrowUpIcon, CheckIcon } from "@phosphor-icons/react";
import { profile } from "../../data";
import { Item, Reveal, Section } from "../Section";
import { spring } from "../motion";
import { AgentGraph } from "./AgentGraph";
import { Mascot } from "./Mascot";
import { MASCOT_NAME, mascotState } from "./mascotMood";
import { Message } from "./Messages";
import { clearGlow, glowSections, sectionOf } from "./highlight";
import { DEMO_PROMPTS, MORE_PROMPTS } from "./samples";
import { useAgent } from "./useAgent";

function formatDetail(detail) {
  if (detail == null) return "";
  if (Array.isArray(detail)) return detail.map((d) => d.id).join(", ") || "no matches";
  if (typeof detail === "object")
    return Object.entries(detail)
      .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.length : v}`)
      .join(" · ");
  return String(detail);
}

function citedIds(m) {
  if (!m || m.streaming) return [];
  if (m.kind === "relevance") return m.items.filter((i) => i.covered).flatMap((i) => i.citations);
  if (m.kind === "answer") return [...(m.text || "").matchAll(/\[([a-z0-9-]+)\]/g)].map((x) => x[1]);
  return [];
}

function StatusBadge({ health }) {
  const map = {
    checking: ["Connecting", "bg-muted", false],
    waking: ["Waking server (free tier, up to a minute)", "bg-muted", true],
    offline: ["Offline", "bg-muted", false],
    ready: [health.demo ? "Demo mode · no LLM key" : `Live · ${health.model}`, "bg-mint", true],
  };
  const [label, dot, breathing] = map[health.status];
  return (
    <span className="inline-flex items-center gap-2 font-mono text-[0.6875rem] text-muted">
      <span className={`relative h-1.5 w-1.5 rounded-full ${dot} ${breathing ? "breathe" : ""}`} />
      {label}
    </span>
  );
}

export function AgentSection() {
  const { health, messages, nodes, trace, run, send, reset } = useAgent();
  const [input, setInput] = useState("");
  const [glowCount, setGlowCount] = useState(0);
  const scrollRef = useRef(null);
  const running = run.state === "running";

  // Let the post-answer reaction (hearts, head tilt) play for a few seconds, then relax to idle.
  const [settled, setSettled] = useState(false);
  useEffect(() => {
    setSettled(false);
    if (run.state !== "finished") return;
    const t = setTimeout(() => setSettled(true), 5000);
    return () => clearTimeout(t);
  }, [run.state]);
  const mascot = mascotState({ health, run, messages, nodes, settled });

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, run.state]);

  // After each answer, suggest prompts the visitor hasn't tried yet (starters first, then more).
  const asked = new Set(messages.filter((m) => m.role === "user").map((m) => m.text.trim()));
  const nextPrompts = [...DEMO_PROMPTS, ...MORE_PROMPTS].filter((p) => !asked.has((p.message || p.label).trim())).slice(0, 3);

  // Glow the cited sections of the page once an answer or role match lands.
  const last = messages[messages.length - 1];
  useEffect(() => {
    const ids = [...new Set(citedIds(last).map(sectionOf))].filter((id) => id !== "top");
    if (!ids.length) return;
    glowSections(ids);
    setGlowCount(ids.length);
  }, [last]);

  const submit = (text) => {
    if (running || !text.trim()) return;
    clearGlow();
    setGlowCount(0);
    send(text);
    setInput("");
  };

  // Prompts handed over from elsewhere on the page (the hero console).
  const submitRef = useRef(submit);
  submitRef.current = submit;
  useEffect(() => {
    const onAsk = (e) => submitRef.current(e.detail);
    window.addEventListener("agent:ask", onAsk);
    return () => window.removeEventListener("agent:ask", onAsk);
  }, []);

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit(input);
    }
  };

  const startOver = () => {
    reset();
    clearGlow();
    setGlowCount(0);
  };

  return (
    <Section
      id="agent"
      index="03"
      title="Ask my agent"
      kicker="Ask what a resume can't answer: how things were built, why, and what went wrong. A LangGraph multi-agent system grounded in this page."
    >
      <Reveal className="grid overflow-hidden rounded-[1.75rem] border border-line bg-surface shadow-[var(--shadow),var(--edge)] lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        {/* Graph + trace */}
        <div className="border-b border-line p-5 md:p-6 lg:border-r lg:border-b-0">
          <div className="mb-3 flex items-center justify-between">
            <span className="font-mono text-[0.6875rem] tracking-wider text-muted uppercase">Agent graph</span>
            <StatusBadge health={health} />
          </div>
          <AgentGraph nodes={nodes} run={run} />
          <div className="mt-4 border-t border-line pt-3">
            <div className="mb-2 flex justify-between font-mono text-[0.6875rem] tracking-wider text-muted uppercase">
              <span>Trace</span>
              {run.ms != null && <span>{(run.ms / 1000).toFixed(1)}s total</span>}
            </div>
            <ol className="min-h-[5.5rem] space-y-1 font-mono text-[0.6875rem]">
              {trace.length === 0 && <li className="text-muted">Each step appears here with its timing.</li>}
              {trace.map((t, i) => (
                <li key={i} className="trace-line flex gap-2">
                  <span className="w-28 shrink-0 text-accent">{t.node}</span>
                  <span className="w-12 shrink-0 text-right text-muted">{t.ms}ms</span>
                  <span className="truncate text-muted" title={formatDetail(t.detail)}>
                    {formatDetail(t.detail)}
                  </span>
                </li>
              ))}
            </ol>
          </div>
          {/* how answers are kept honest, stated plainly */}
          <ul className="mt-4 space-y-1.5 border-t border-line pt-3 text-xs text-muted">
            {[
              "Every claim cites the section it came from",
              "Citations are checked against the sources before you see them",
              "Retrieval and routing are covered by a regression test suite",
            ].map((t) => (
              <li key={t} className="flex items-start gap-2">
                <CheckIcon size={13} className="mt-0.5 shrink-0 text-mint" />
                {t}
              </li>
            ))}
          </ul>
        </div>

        {/* Conversation */}
        <div className="flex min-h-[32rem] flex-col">
          <div className="flex items-center gap-4 border-b border-line px-5 py-4 md:px-6">
            <Mascot mood={mascot.mood} size={76} track className="shrink-0" />
            <div className="min-w-0">
              <p className="font-mono text-[0.6875rem] tracking-wider text-muted uppercase">{MASCOT_NAME} · portfolio agent</p>
              <div className="relative mt-1.5 rounded-2xl rounded-tl-md border border-line bg-bg px-3.5 py-2 text-sm">
                <AnimatePresence mode="wait" initial={false}>
                  <motion.p
                    key={mascot.line}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    transition={spring}
                    aria-live="polite"
                  >
                    {mascot.line}
                  </motion.p>
                </AnimatePresence>
              </div>
            </div>
          </div>
          <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto p-5 md:p-6 lg:max-h-[36rem]">
            {messages.length === 0 ? (
              <Reveal stagger={0.06}>
                <Item as="p" className="text-sm text-muted">
                  Pick a prompt, or paste a job description below.
                </Item>
                <div className="mt-4 flex flex-col items-start gap-2">
                  {DEMO_PROMPTS.map((p) => (
                    <Item
                      as="button"
                      key={p.label}
                      onClick={() => submit(p.message || p.label)}
                      disabled={running}
                      className="rounded-full border border-line px-4 py-2 text-left text-sm transition-colors hover:border-accent hover:text-accent active:scale-[0.98] disabled:opacity-50"
                    >
                      {p.label}
                    </Item>
                  ))}
                </div>
              </Reveal>
            ) : (
              <AnimatePresence initial={false}>
                {messages.map((m, i) => (
                  <motion.div key={i} layout="position" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={spring}>
                    <Message m={m} />
                  </motion.div>
                ))}
                {!running && run.state === "finished" && nextPrompts.length > 0 && (
                  <motion.div
                    key={`next-${messages.length}`}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0, transition: { ...spring, delay: 0.25 } }}
                    exit={{ opacity: 0 }}
                    className="pl-[42px]"
                  >
                    <p className="font-mono text-[0.6875rem] tracking-wider text-muted uppercase">Ask next</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {nextPrompts.map((p) => (
                        <button
                          key={p.label}
                          onClick={() => submit(p.message || p.label)}
                          className="rounded-full border border-line px-3.5 py-1.5 text-left text-sm transition-colors hover:border-accent hover:text-accent active:scale-[0.98]"
                        >
                          {p.label}
                        </button>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            )}
            {health.status === "offline" && (
              <p role="alert" className="rounded-xl border border-line bg-bg p-3 text-sm text-muted">
                The agent server isn&rsquo;t responding right now. You can still reach Taniksha at{" "}
                <a className="text-accent underline" href={`mailto:${profile.email}`}>
                  {profile.email}
                </a>
                .
              </p>
            )}
          </div>

          <AnimatePresence>
            {glowCount > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={spring}
                className="overflow-hidden border-t border-line"
              >
                <div className="flex items-center justify-between px-5 py-2 font-mono text-[0.6875rem] text-muted md:px-6">
                  <span className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                    {glowCount} matching section{glowCount > 1 ? "s" : ""} highlighted on the page
                  </span>
                  <button
                    onClick={() => {
                      clearGlow();
                      setGlowCount(0);
                    }}
                    className="hover:text-ink"
                  >
                    Clear
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="border-t border-line p-3">
            <label htmlFor="agent-input" className="sr-only">
              Message the portfolio agent
            </label>
            <div className="flex items-end gap-2 rounded-2xl border border-line bg-bg p-2 transition-colors focus-within:border-accent">
              <textarea
                id="agent-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                rows={input.includes("\n") ? 5 : 1}
                maxLength={6000}
                placeholder="Ask about my work, or paste a job description"
                className="max-h-48 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm outline-none placeholder:text-muted"
              />
              {messages.length > 0 && (
                <button
                  onClick={startOver}
                  disabled={running}
                  className="rounded-xl p-2 text-muted transition-all hover:text-ink active:scale-[0.94] disabled:opacity-40"
                  aria-label="Start over"
                >
                  <ArrowCounterClockwiseIcon size={16} />
                </button>
              )}
              <button
                onClick={() => submit(input)}
                disabled={running || !input.trim()}
                className="rounded-xl bg-ink p-2 text-bg transition-all active:scale-[0.94] disabled:opacity-30"
                aria-label="Send"
              >
                <ArrowUpIcon size={16} />
              </button>
            </div>
          </div>
        </div>
      </Reveal>
    </Section>
  );
}
