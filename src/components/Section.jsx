import { motion, useMotionValue, useReducedMotion, useSpring } from "framer-motion";
import { spring } from "./motion";

const rise = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: spring },
};

// Fades/rises once when scrolled into view. Pass `stagger` to cascade direct <Item> children.
export function Reveal({ as = "div", stagger, className = "", children, ...rest }) {
  const reduce = useReducedMotion();
  const Tag = motion[as];
  return (
    <Tag
      className={className}
      initial={reduce ? false : "hidden"}
      whileInView="show"
      viewport={{ once: true, amount: 0.15 }}
      variants={stagger ? { hidden: {}, show: { transition: { staggerChildren: stagger } } } : rise}
      {...rest}
    >
      {children}
    </Tag>
  );
}

export function Item({ as = "div", className = "", children, ...rest }) {
  const Tag = motion[as];
  return (
    <Tag className={className} variants={rise} {...rest}>
      {children}
    </Tag>
  );
}

export function Section({ id, index, title, kicker, children }) {
  return (
    <section id={id} className="mx-auto max-w-6xl px-4 py-12 sm:px-6 md:py-16">
      <Reveal className="mb-8 grid gap-4 md:mb-10 md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] md:items-end">
        <div className="flex items-baseline gap-3">
          <span className="font-mono text-xs text-accent">{index}</span>
          <h2 className="text-4xl font-semibold leading-none tracking-tight md:text-5xl">{title}</h2>
        </div>
        {kicker && <p className="max-w-[60ch] leading-relaxed text-muted md:justify-self-end md:text-right">{kicker}</p>}
      </Reveal>
      {children}
    </section>
  );
}

export function Tag({ children }) {
  return (
    <span className="rounded-full border border-line bg-surface px-2.5 py-1 font-mono text-[0.6875rem] text-muted">
      {children}
    </span>
  );
}

// Pulls toward the cursor using motion values, so pointer movement never re-renders React.
export function Magnetic({ children, strength = 0.25, className = "" }) {
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const sx = useSpring(x, { stiffness: 150, damping: 15, mass: 0.1 });
  const sy = useSpring(y, { stiffness: 150, damping: 15, mass: 0.1 });
  const reduce = useReducedMotion();

  const onMove = (e) => {
    if (reduce) return;
    const r = e.currentTarget.getBoundingClientRect();
    x.set((e.clientX - (r.left + r.width / 2)) * strength);
    y.set((e.clientY - (r.top + r.height / 2)) * strength);
  };
  const reset = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div className={`inline-block ${className}`} style={{ x: sx, y: sy }} onPointerMove={onMove} onPointerLeave={reset}>
      {children}
    </motion.div>
  );
}
