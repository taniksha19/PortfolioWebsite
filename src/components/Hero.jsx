import { motion, useReducedMotion } from "framer-motion";
import { EnvelopeIcon, FileTextIcon, GithubLogoIcon, LinkedinLogoIcon } from "@phosphor-icons/react";
import { profile } from "../data";
import { HeroConsole } from "./HeroConsole";
import { MeAndNimbus } from "./MeAndNimbus";
import { Doodles } from "./Doodles";
import { Item, Magnetic, Reveal } from "./Section";
import { spring } from "./motion";

const iconLink =
  "inline-flex h-11 w-11 items-center justify-center rounded-full border border-line bg-surface text-muted transition-all duration-300 hover:border-accent hover:text-ink active:scale-[0.98]";

export function Hero() {
  const reduce = useReducedMotion();

  return (
    <section id="top" className="mx-auto flex min-h-[100dvh] max-w-6xl flex-col justify-center px-4 pt-28 pb-8 sm:px-6">
      <div className="relative grid items-center gap-12 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] md:gap-12">
        <Doodles />
        <Reveal stagger={0.08}>
          <Item as="p" className="flex items-center gap-2 font-mono text-xs text-muted">
            <span className="breathe relative h-1.5 w-1.5 rounded-full bg-mint" />
            MS CS @ Northeastern · graduating Dec 2026 · {profile.location}
          </Item>
          <Item as="h1" className="mt-6 text-5xl font-semibold leading-none tracking-tight md:text-6xl">
            {profile.name}
          </Item>
          <Item as="p" className="mt-4 font-mono text-sm text-accent">
            {profile.role} / {profile.focus.join(" / ")}
          </Item>
          <Item as="p" className="mt-6 max-w-[52ch] text-lg leading-relaxed text-muted">
            {profile.intro}
          </Item>
          <Item className="mt-9 flex flex-wrap items-center gap-3">
            <Magnetic>
              <a
                href={`mailto:${profile.email}`}
                className="inline-flex items-center gap-2 rounded-full bg-ink px-6 py-3 text-sm font-medium text-bg transition-transform active:scale-[0.98]"
              >
                <EnvelopeIcon size={16} /> Get in touch
              </a>
            </Magnetic>
            <a
              href={profile.resume}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-5 py-3 text-sm font-medium transition-all duration-300 hover:border-accent active:scale-[0.98]"
            >
              <FileTextIcon size={16} /> Resume
            </a>
            <a href={profile.github} target="_blank" rel="noreferrer" className={iconLink} aria-label="GitHub">
              <GithubLogoIcon size={18} />
            </a>
            <a href={profile.linkedin} target="_blank" rel="noreferrer" className={iconLink} aria-label="LinkedIn">
              <LinkedinLogoIcon size={18} />
            </a>
          </Item>
        </Reveal>

        <div className="relative flex flex-col items-center gap-6 lg:block">
          <Doodles group="console" />
          <motion.div
            initial={reduce ? false : { opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...spring, delay: 0.2 }}
            className="w-40 sm:w-48 lg:absolute lg:-bottom-6 lg:-left-6 lg:z-10 lg:w-52"
          >
            <MeAndNimbus />
          </motion.div>
          <motion.div
            initial={reduce ? false : { opacity: 0, y: 24, rotate: 1.5 }}
            animate={{ opacity: 1, y: 0, rotate: 0 }}
            transition={{ ...spring, delay: 0.35 }}
            className="w-full lg:ml-auto lg:w-[calc(100%-10rem)] lg:pt-40"
          >
            <HeroConsole />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
