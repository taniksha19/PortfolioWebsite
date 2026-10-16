import { useState } from "react";
import { CheckIcon, CopyIcon, EnvelopeIcon, WarningCircleIcon } from "@phosphor-icons/react";
import { Mascot } from "./Mascot";
import { flashSection } from "./highlight";

const shortTitle = (t) => t.replace(/^(Project|Skills|Education): /, "");
const titleMap = (sources = []) => Object.fromEntries(sources.map((s) => [s.id, shortTitle(s.title)]));

function Cite({ id, titles }) {
  return (
    <button
      onClick={() => flashSection(id)}
      className="mx-0.5 inline-flex translate-y-[-1px] items-center rounded-md border border-line bg-bg px-1.5 py-0.5 align-middle font-mono text-[0.625rem] text-accent transition-all hover:border-accent active:scale-[0.96]"
      title="Show this section on the page"
    >
      {titles[id] || id}
    </button>
  );
}

function CitedText({ text, sources = [] }) {
  const titles = titleMap(sources);
  const parts = text.split(/\[([a-z0-9-]+)\]/g);
  const shown = new Set(); // show each source once, at its first citation
  return (
    <p className="whitespace-pre-wrap leading-relaxed">
      {parts.map((part, i) => {
        if (i % 2 === 0) return part;
        if (shown.has(part)) return null;
        shown.add(part);
        return <Cite key={i} id={part} titles={titles} />;
      })}
    </p>
  );
}

// Points to the relevant work for each requirement. No scores: an agent built by the candidate
// shouldn't grade the candidate.
function RelevanceCard({ m }) {
  const titles = titleMap(m.sources);
  const covered = m.items.filter((i) => i.covered);
  const notShown = m.items.filter((i) => !i.covered);
  return (
    <div className="space-y-4">
      <div>
        <p className="font-mono text-[0.6875rem] tracking-wider text-accent uppercase">Where to look · {m.role_title}</p>
        <p className="mt-2 leading-relaxed">{m.summary}</p>
      </div>
      {covered.length > 0 && (
        <ul className="divide-y divide-line rounded-xl border border-line">
          {covered.map((item, i) => (
            <li key={i} className="flex gap-3 p-3">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              <div className="min-w-0">
                <p className="text-sm font-medium">{item.requirement}</p>
                <p className="mt-1 text-sm text-muted">
                  {item.evidence}
                  {item.citations.map((c) => (
                    <Cite key={c} id={c} titles={titles} />
                  ))}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
      {notShown.length > 0 && (
        <p className="text-sm text-muted">
          <span className="font-mono text-[0.6875rem] tracking-wider uppercase">Not shown in the portfolio: </span>
          {notShown.map((i) => i.requirement).join("; ")}
        </p>
      )}
    </div>
  );
}

function EmailCard({ m }) {
  const [copied, setCopied] = useState(false);
  const mailto = `mailto:${m.to}?subject=${encodeURIComponent(m.subject)}&body=${encodeURIComponent(m.body)}`;
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(`${m.subject}\n\n${m.body}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // Clipboard blocked; the mailto button still works.
    }
  };
  return (
    <div className="space-y-3">
      <p className="font-mono text-[0.6875rem] uppercase tracking-wider text-accent">Draft email · to {m.to}</p>
      <div className="rounded-xl border border-line bg-bg p-4 text-sm">
        <p className="font-medium">{m.subject}</p>
        <p className="mt-3 whitespace-pre-wrap leading-relaxed text-muted">{m.body}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <a href={mailto} className="inline-flex items-center gap-2 rounded-full bg-ink px-4 py-2 text-xs font-medium text-bg transition-transform active:scale-[0.98]">
          <EnvelopeIcon size={14} /> Open in email app
        </a>
        <button onClick={copy} className="inline-flex items-center gap-2 rounded-full border border-line px-4 py-2 text-xs transition-all hover:border-accent active:scale-[0.98]">
          {copied ? <CheckIcon size={14} /> : <CopyIcon size={14} />} {copied ? "Copied" : "Copy"}
        </button>
      </div>
    </div>
  );
}

export function Message({ m }) {
  if (m.role === "user") {
    return (
      <div className="ml-auto max-w-[85%] rounded-2xl rounded-br-md bg-ink px-4 py-2.5 text-sm text-bg">
        <p className="line-clamp-6 whitespace-pre-wrap">{m.text}</p>
      </div>
    );
  }
  if (m.kind === "error") {
    return (
      <div role="alert" className="flex items-start gap-2 rounded-xl border border-line bg-bg p-3 text-sm text-muted">
        <WarningCircleIcon size={16} className="mt-0.5 shrink-0 text-accent" /> {m.text}
      </div>
    );
  }
  return (
    <div className="flex gap-3 text-sm">
      <span className="mt-0.5 shrink-0">
        <Mascot size={30} still />
      </span>
      <div className="min-w-0 flex-1">
        {m.kind === "relevance" && <RelevanceCard m={m} />}
        {m.kind === "email" && <EmailCard m={m} />}
        {m.kind === "answer" &&
          (m.text ? (
            <CitedText text={m.text} sources={m.sources} />
          ) : (
            <div className="space-y-2 pt-1.5" aria-label="Agent is working">
              <div className="skeleton h-3 w-11/12" />
              <div className="skeleton h-3 w-4/5" />
              <div className="skeleton h-3 w-2/5" />
            </div>
          ))}
      </div>
    </div>
  );
}
