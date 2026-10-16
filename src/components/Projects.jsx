import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ArrowUpRightIcon, ArrowsOutSimpleIcon, CaretLeftIcon, CaretRightIcon, GithubLogoIcon, XIcon } from "@phosphor-icons/react";
import { profile, projects } from "../data";
import { Item, Reveal, Section, Tag } from "./Section";
import { spring, trackSpotlight } from "./motion";

const featured = projects.filter((p) => p.tier !== "more");
const more = projects.filter((p) => p.tier === "more");

function Bullets({ items, className = "" }) {
  return (
    <ul className={`space-y-2.5 text-sm text-muted ${className}`}>
      {items.map((pt) => (
        <li key={pt} className="relative pl-5 leading-relaxed">
          <span className="absolute top-[0.75em] left-0 h-px w-2.5 bg-accent" />
          {pt}
        </li>
      ))}
    </ul>
  );
}

// Compact card; clicking morphs it (shared layoutId) into the detail dialog.
function ProjectCard({ p, onOpen }) {
  const shown = p.stack.slice(0, 3);
  const extra = p.stack.length - shown.length;
  return (
    <Item id={p.id} className="h-full">
      <motion.button
        layoutId={`card-${p.id}`}
        onClick={onOpen}
        onPointerMove={trackSpotlight}
        aria-haspopup="dialog"
        className="spotlight group flex h-full w-full flex-col rounded-[1.5rem] border border-line bg-surface p-5 text-left shadow-[var(--shadow),var(--edge)] transition-transform active:scale-[0.98]"
        style={{ borderRadius: 24 }}
      >
        <div className="flex items-start justify-between gap-3">
          <motion.p layoutId={`kind-${p.id}`} className="font-mono text-[11px] text-accent">
            {p.kind}
          </motion.p>
          <ArrowsOutSimpleIcon size={16} className="shrink-0 text-muted transition-all duration-300 group-hover:scale-110 group-hover:text-accent" />
        </div>
        <motion.h3 layoutId={`title-${p.id}`} className="mt-2.5 text-xl leading-tight font-semibold tracking-tight">
          {p.title}
        </motion.h3>
        <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-muted">{p.summary}</p>
        <div className="mt-auto flex flex-wrap gap-1.5 pt-5">
          {shown.map((s) => (
            <Tag key={s}>{s}</Tag>
          ))}
          {extra > 0 && <Tag>+{extra}</Tag>}
        </div>
      </motion.button>
    </Item>
  );
}

const slide = {
  enter: (dir) => ({ opacity: 0, x: dir * 40 }),
  center: { opacity: 1, x: 0, transition: spring },
  exit: (dir) => ({ opacity: 0, x: dir * -40, transition: { duration: 0.15 } }),
};

// Opens by morphing out of the clicked card. Arrows (buttons, left/right keys, or a swipe) move between
// projects; after moving, closing fades out instead of morphing back into a different card.
function ProjectDialog({ index, openedFrom, onNavigate, onClose }) {
  const closeRef = useRef(null);
  const reduce = useReducedMotion();
  const p = featured[index];
  const [dir, setDir] = useState(0);
  const morph = !reduce && p.id === openedFrom;
  const prev = featured[(index - 1 + featured.length) % featured.length];
  const next = featured[(index + 1) % featured.length];

  const go = useCallback(
    (step) => {
      setDir(step);
      onNavigate((index + step + featured.length) % featured.length);
    },
    [index, onNavigate]
  );

  useEffect(() => {
    closeRef.current?.focus({ preventScroll: true });
  }, []);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
      else if (e.key === "ArrowRight") go(1);
      else if (e.key === "ArrowLeft") go(-1);
    };
    // The page stays scrollable: scrolling it means the visitor has moved on, so close the card.
    const startY = window.scrollY;
    const onScroll = () => Math.abs(window.scrollY - startY) > 40 && onClose();
    window.addEventListener("keydown", onKey);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("scroll", onScroll);
    };
  }, [onClose, go]);

  const navButton =
    "rounded-full border border-line bg-[var(--bg)] p-2.5 text-muted transition-all hover:border-accent hover:text-accent active:scale-[0.94]";

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 sm:p-6">
      <motion.div
        className="absolute inset-0 bg-ink/25 backdrop-blur-sm"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      />
      <motion.div
        layoutId={morph ? `card-${p.id}` : undefined}
        initial={morph ? undefined : { opacity: 0, scale: 0.97 }}
        animate={morph ? undefined : { opacity: 1, scale: 1 }}
        exit={morph ? undefined : { opacity: 0, scale: 0.97 }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="project-dialog-title"
        transition={spring}
        className="relative flex max-h-[min(44rem,calc(100dvh-2rem))] w-full max-w-2xl flex-col overflow-hidden border border-line bg-[var(--bg)] shadow-[var(--shadow),var(--edge)]"
        style={{ borderRadius: 28 }}
      >
        {/* pinned outside the scroll area so it stays reachable */}
        <button
          ref={closeRef}
          onClick={onClose}
          aria-label="Close project details"
          className={`absolute top-4 right-4 z-10 sm:top-6 sm:right-6 ${navButton}`}
        >
          <XIcon size={16} />
        </button>

        <div className="min-h-0 flex-1 overflow-x-hidden overflow-y-auto p-6 sm:p-9" data-dialog-scroll>
          <AnimatePresence mode="wait" custom={dir} initial={false}>
            <motion.div
              key={p.id}
              custom={dir}
              variants={reduce ? undefined : slide}
              initial="enter"
              animate="center"
              exit="exit"
              drag={reduce ? false : "x"}
              dragConstraints={{ left: 0, right: 0 }}
              dragElastic={0.18}
              onDragEnd={(_, info) => {
                if (info.offset.x < -70) go(1);
                else if (info.offset.x > 70) go(-1);
              }}
            >
              <div className="pr-12">
                <motion.p layoutId={morph ? `kind-${p.id}` : undefined} className="font-mono text-xs text-accent">
                  {p.kind}
                </motion.p>
                <motion.h3
                  layoutId={morph ? `title-${p.id}` : undefined}
                  id="project-dialog-title"
                  className="mt-3 text-3xl leading-none font-semibold tracking-tight"
                >
                  {p.title}
                </motion.h3>
              </div>
              <p className="mt-6 max-w-[60ch] leading-relaxed">{p.summary}</p>
              <Bullets items={p.points} className="mt-6" />
              <div className="mt-7 flex flex-wrap gap-2">
                {p.stack.map((s) => (
                  <Tag key={s}>{s}</Tag>
                ))}
              </div>
              <a
                href={p.link}
                target="_blank"
                rel="noreferrer"
                className="group mt-8 inline-flex items-center gap-2 rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-bg transition-transform active:scale-[0.98]"
              >
                <GithubLogoIcon size={16} /> View on GitHub
                <ArrowUpRightIcon size={14} className="transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </a>
            </motion.div>
          </AnimatePresence>
        </div>

        <div className="flex items-center justify-between gap-4 border-t border-line px-6 py-3 sm:px-9">
          <button onClick={() => go(-1)} aria-label={`Previous project: ${prev.title}`} className={navButton}>
            <CaretLeftIcon size={16} />
          </button>
          <div className="flex items-center gap-3">
            <div className="flex gap-1.5" aria-hidden="true">
              {featured.map((f, i) => (
                <span key={f.id} className={`h-1.5 rounded-full transition-all duration-300 ${i === index ? "w-5 bg-accent" : "w-1.5 bg-line"}`} />
              ))}
            </div>
            <span className="font-mono text-xs text-muted" aria-live="polite">
              {index + 1} / {featured.length}
            </span>
          </div>
          <button onClick={() => go(1)} aria-label={`Next project: ${next.title}`} className={navButton}>
            <CaretRightIcon size={16} />
          </button>
        </div>
      </motion.div>
    </div>
  );
}

export function Projects() {
  const [openIndex, setOpenIndex] = useState(null);
  const [openedFrom, setOpenedFrom] = useState(null);
  const lastCard = useRef(null);

  const close = useCallback(() => {
    setOpenIndex(null);
    // return focus to the card that opened the dialog, without jumping the page back to it
    requestAnimationFrame(() => lastCard.current?.querySelector("button")?.focus({ preventScroll: true }));
  }, []);

  return (
    <Section id="projects" index="02" title="Projects" kicker="LLM safety, multilingual NLP and ML from first principles, plus the full-stack work underneath.">
      <Reveal stagger={0.08} className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {featured.map((p, i) => (
          <ProjectCard
            key={p.id}
            p={p}
            onOpen={(e) => {
              lastCard.current = e.currentTarget.parentElement;
              setOpenedFrom(p.id);
              setOpenIndex(i);
            }}
          />
        ))}
      </Reveal>

      <AnimatePresence>
        {openIndex !== null && (
          <ProjectDialog key="project-dialog" index={openIndex} openedFrom={openedFrom} onNavigate={setOpenIndex} onClose={close} />
        )}
      </AnimatePresence>

      {more.length > 0 && (
        <>
          <Reveal className="mt-12 mb-4 flex items-baseline justify-between gap-4">
            <h3 className="font-mono text-xs tracking-wider text-muted uppercase">More on GitHub</h3>
            <a
              href={profile.github}
              target="_blank"
              rel="noreferrer"
              className="group inline-flex items-center gap-1 font-mono text-xs text-accent"
            >
              All repositories
              <ArrowUpRightIcon size={12} className="transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </a>
          </Reveal>
          {/* One compact row per repo: title and type, a one-line summary, the stack. */}
          <Reveal as="ul" stagger={0.06} className="divide-y divide-line border-y border-line">
            {more.map((p) => (
              <Item as="li" key={p.id} id={p.id}>
                <a
                  href={p.link}
                  target="_blank"
                  rel="noreferrer"
                  className="group grid items-center gap-x-8 gap-y-1 px-1 py-4 md:grid-cols-[minmax(0,15rem)_minmax(0,1fr)_auto] md:px-4"
                >
                  <div className="min-w-0">
                    <h4 className="truncate font-semibold tracking-tight transition-colors group-hover:text-accent">{p.title}</h4>
                    <p className="font-mono text-[11px] text-accent">{p.kind}</p>
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm text-muted md:text-ink">{p.summary}</p>
                    <p className="mt-0.5 truncate font-mono text-[11px] text-muted">{p.stack.join(" · ")}</p>
                  </div>
                  <ArrowUpRightIcon
                    size={16}
                    className="hidden text-muted transition-all duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-accent md:block"
                  />
                </a>
              </Item>
            ))}
          </Reveal>
        </>
      )}
    </Section>
  );
}
