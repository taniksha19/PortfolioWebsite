import { useState } from "react";
import { AnimatePresence, motion, useMotionValueEvent, useScroll } from "framer-motion";
import { ListIcon, MoonIcon, SunIcon, XIcon } from "@phosphor-icons/react";
import { spring } from "./motion";

const links = [
  { href: "#experience", label: "Experience" },
  { href: "#projects", label: "Projects" },
  { href: "#agent", label: "Ask my agent" },
  { href: "#skills", label: "Skills" },
  { href: "#contact", label: "Contact" },
];

function currentTheme() {
  const set = document.documentElement.dataset.theme;
  if (set) return set;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function Nav() {
  const [theme, setTheme] = useState(currentTheme);
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { scrollY } = useScroll();
  useMotionValueEvent(scrollY, "change", (y) => setScrolled(y > 12));

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("theme", next);
    } catch {
      // Storage unavailable; theme still applies for this visit.
    }
    setTheme(next);
  };

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 border-b transition-colors duration-300 ${
        scrolled || open ? "border-line bg-bg/80 backdrop-blur-md" : "border-transparent"
      }`}
    >
      <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <a href="#top" className="font-display text-xl font-semibold tracking-tight" aria-label="Back to top">
          td<span className="text-accent">.</span>
        </a>

        <div className="flex items-center gap-1">
          <ul className="hidden items-center gap-1 md:flex">
            {links.map((l) => (
              <li key={l.href}>
                <a href={l.href} className="rounded-full px-3 py-2 text-sm text-muted transition-colors hover:text-ink">
                  {l.label}
                </a>
              </li>
            ))}
          </ul>
          <button
            onClick={toggleTheme}
            className="rounded-full p-2.5 text-muted transition-all hover:text-ink active:scale-[0.94]"
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            {theme === "dark" ? <SunIcon size={18} /> : <MoonIcon size={18} />}
          </button>
          <button
            onClick={() => setOpen((o) => !o)}
            className="rounded-full p-2.5 text-muted hover:text-ink active:scale-[0.94] md:hidden"
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
          >
            {open ? <XIcon size={20} /> : <ListIcon size={20} />}
          </button>
        </div>
      </nav>

      <AnimatePresence>
        {open && (
          <motion.ul
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0, transition: { ...spring, staggerChildren: 0.04 } }}
            exit={{ opacity: 0, y: -8 }}
            className="border-t border-line px-4 py-3 md:hidden"
          >
            {links.map((l) => (
              <motion.li key={l.href} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={spring}>
                <a href={l.href} onClick={() => setOpen(false)} className="block py-3 text-2xl font-semibold tracking-tight">
                  {l.label}
                </a>
              </motion.li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </header>
  );
}
