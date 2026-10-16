import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowUpRightIcon, CheckIcon, CopyIcon } from "@phosphor-icons/react";
import { profile } from "../data";
import { Item, Magnetic, Reveal, Section } from "./Section";
import { spring } from "./motion";

export function Contact() {
  const [copied, setCopied] = useState(false);

  const copyEmail = async () => {
    try {
      await navigator.clipboard.writeText(profile.email);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      window.location.href = `mailto:${profile.email}`;
    }
  };

  const links = [
    { label: "LinkedIn", href: profile.linkedin },
    { label: "GitHub", href: profile.github },
    { label: "Resume", href: profile.resume },
  ];

  return (
    <Section id="contact" index="05" title="Contact">
      <Reveal stagger={0.08} className="grid gap-12 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)] md:items-end">
        <div>
          <Item as="p" className="max-w-[48ch] text-lg leading-relaxed text-muted">
            Building something with LLMs, retrieval or agents? I&rsquo;d like to hear about it.
          </Item>
          <Item className="mt-8 flex flex-wrap items-center gap-3">
            <a
              href={`mailto:${profile.email}`}
              className="font-display text-3xl font-semibold tracking-tight break-all underline decoration-line decoration-1 underline-offset-[10px] transition-colors hover:decoration-accent sm:text-5xl"
            >
              {profile.email}
            </a>
            <Magnetic strength={0.35}>
              <button
                onClick={copyEmail}
                className="relative flex h-11 w-11 items-center justify-center rounded-full border border-line text-muted transition-colors hover:border-accent hover:text-accent active:scale-[0.94]"
                aria-label={copied ? "Email copied" : "Copy email address"}
              >
                <AnimatePresence mode="wait" initial={false}>
                  <motion.span
                    key={copied ? "check" : "copy"}
                    initial={{ scale: 0.5, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.5, opacity: 0 }}
                    transition={spring}
                  >
                    {copied ? <CheckIcon size={16} /> : <CopyIcon size={16} />}
                  </motion.span>
                </AnimatePresence>
              </button>
            </Magnetic>
          </Item>
        </div>
        <Item as="ul" className="flex flex-col divide-y divide-line border-y border-line">
          {links.map((l) => (
            <li key={l.label}>
              <a
                href={l.href}
                target="_blank"
                rel="noreferrer"
                className="group flex items-center justify-between py-4 font-mono text-sm text-muted transition-colors hover:text-accent"
              >
                {l.label}
                <ArrowUpRightIcon size={14} className="transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </a>
            </li>
          ))}
        </Item>
      </Reveal>
    </Section>
  );
}
