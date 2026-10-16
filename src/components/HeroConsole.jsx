import { memo, useEffect, useRef } from "react";
import { useReducedMotion } from "framer-motion";
import { ArrowRightIcon } from "@phosphor-icons/react";
import { DEMO_PROMPTS, askAgent } from "./agent/samples";

const STEPS = ["router", "retriever", "extractor", "matcher", "answerer", "contact_drafter", "citation_check"];
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// A self-running preview of the agent. All animation writes go straight to the DOM through refs,
// so the loop never re-renders React.
export const HeroConsole = memo(function HeroConsole() {
  const textRef = useRef(null);
  const stepsRef = useRef(null);
  const busyRef = useRef(null);
  const current = useRef(DEMO_PROMPTS[0]);
  const reduce = useReducedMotion();

  useEffect(() => {
    let alive = true;
    const setStep = (name, state) => {
      const el = stepsRef.current?.querySelector(`[data-step="${name}"]`);
      if (el) el.dataset.state = state;
    };

    async function loop() {
      for (let i = 0; alive; i = (i + 1) % DEMO_PROMPTS.length) {
        const prompt = DEMO_PROMPTS[i];
        current.current = prompt;
        STEPS.forEach((s) => setStep(s, prompt.path.includes(s) ? "idle" : "off"));
        textRef.current.textContent = "";
        busyRef.current.dataset.on = "false";

        if (reduce) {
          textRef.current.textContent = prompt.label;
          prompt.path.forEach((s) => setStep(s, "done"));
          await wait(5000);
          continue;
        }
        for (const ch of prompt.label) {
          if (!alive) return;
          textRef.current.textContent += ch;
          await wait(28 + Math.random() * 40);
        }
        await wait(500);
        busyRef.current.dataset.on = "true";
        for (const s of prompt.path) {
          if (!alive) return;
          setStep(s, "active");
          await wait(520);
          setStep(s, "done");
        }
        busyRef.current.dataset.on = "false";
        await wait(2600);
      }
    }
    loop();
    return () => {
      alive = false;
    };
  }, [reduce]);

  return (
    <div className="relative rounded-[1.75rem] border border-line bg-surface p-5 shadow-[var(--shadow),var(--edge)] md:p-6">
      <div className="flex items-center justify-between font-mono text-[0.6875rem] text-muted">
        <span>portfolio-agent</span>
        <span className="flex items-center gap-2">
          <span className="breathe relative h-1.5 w-1.5 rounded-full bg-mint" />
          LangGraph
        </span>
      </div>

      <div className="mt-6 min-h-[4.5rem] text-lg font-medium leading-snug tracking-tight md:text-xl">
        <span ref={textRef} />
        <span className="caret ml-0.5 inline-block h-5 w-[2px] translate-y-1 bg-accent" />
      </div>

      <div ref={busyRef} data-on="false" className="group mt-3 h-1.5">
        <div className="skeleton h-1.5 w-full opacity-0 transition-opacity duration-300 group-data-[on=true]:opacity-100" />
      </div>

      <ol ref={stepsRef} className="mt-5 flex flex-wrap gap-1.5 font-mono text-[0.65625rem]">
        {STEPS.map((s) => (
          <li
            key={s}
            data-step={s}
            data-state="off"
            className="rounded-md border border-line px-2 py-1 text-muted transition-all duration-300 data-[state=off]:hidden data-[state=active]:border-accent data-[state=active]:text-ink data-[state=done]:border-transparent data-[state=done]:bg-accent-soft data-[state=done]:text-accent"
          >
            {s}
          </li>
        ))}
      </ol>

      <button
        onClick={() => askAgent(current.current)}
        className="group mt-6 inline-flex items-center gap-2 text-sm font-medium text-accent transition-transform active:scale-[0.98]"
      >
        Run this for real
        <ArrowRightIcon size={16} className="transition-transform duration-300 group-hover:translate-x-1" />
      </button>
    </div>
  );
});
