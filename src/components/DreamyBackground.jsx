import { memo, useEffect } from "react";
import { motion, useMotionValue, useReducedMotion, useSpring, useTransform } from "framer-motion";

// Fixed positions (percent of viewport) so the sky looks the same on every visit.
// Kept sparse on purpose: a light texture, spread around the edges, not confetti.
const SPARKLES = [
  [8, 14, 16, 0], [57, 9, 14, 3.1], [74, 22, 17, 0.3],
  [14, 46, 10, 2.9], [91, 40, 15, 3.6], [22, 72, 11, 1.2],
  [83, 78, 12, 2.2], [48, 86, 12, 0.6], [4, 88, 14, 3.3],
];
const SPARKLE_COLORS = ["var(--sparkle)", "var(--sparkle-pink)", "var(--sparkle)", "var(--mint)"];

const BLOBS = [
  { color: "var(--blob-1)", size: "62vmax", top: "-18%", left: "-14%", anim: "drift-a 26s ease-in-out infinite", depth: 18 },
  { color: "var(--blob-2)", size: "52vmax", top: "38%", left: "58%", anim: "drift-b 32s ease-in-out infinite", depth: -24 },
  { color: "var(--blob-3)", size: "46vmax", top: "62%", left: "-6%", anim: "drift-c 29s ease-in-out infinite", depth: 12 },
  { color: "var(--blob-1)", size: "38vmax", top: "-10%", left: "62%", anim: "drift-c 36s ease-in-out infinite reverse", depth: -14 },
];

function Star({ size }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 0c.6 6.2 5.8 11.4 12 12-6.2.6-11.4 5.8-12 12-.6-6.2-5.8-11.4-12-12C6.2 11.4 11.4 6.2 12 0z" />
    </svg>
  );
}

function Layer({ depth, px, py, children }) {
  const x = useTransform(px, (v) => v * depth);
  const y = useTransform(py, (v) => v * depth);
  return (
    <motion.div className="absolute inset-0" style={{ x, y }}>
      {children}
    </motion.div>
  );
}

// Pastel blobs drift on CSS keyframes (transform only, radial gradients instead of blur filters);
// the cursor adds a light parallax through motion values, outside React's render cycle.
export const DreamyBackground = memo(function DreamyBackground() {
  const reduce = useReducedMotion();
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const px = useSpring(mx, { stiffness: 40, damping: 20 });
  const py = useSpring(my, { stiffness: 40, damping: 20 });

  useEffect(() => {
    if (reduce) return;
    const onMove = (e) => {
      mx.set(e.clientX / window.innerWidth - 0.5);
      my.set(e.clientY / window.innerHeight - 0.5);
    };
    window.addEventListener("pointermove", onMove, { passive: true });
    return () => window.removeEventListener("pointermove", onMove);
  }, [reduce, mx, my]);

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      {BLOBS.map((b, i) => (
        <Layer key={i} depth={b.depth} px={px} py={py}>
          <div
            className="blob"
            style={{
              width: b.size,
              height: b.size,
              top: b.top,
              left: b.left,
              background: `radial-gradient(circle at center, ${b.color} 0%, transparent 68%)`,
              animation: b.anim,
            }}
          />
        </Layer>
      ))}
      <Layer depth={-30} px={px} py={py}>
        {SPARKLES.map(([left, top, size, delay], i) => (
          <span
            key={i}
            className="sparkle"
            style={{
              left: `${left}%`,
              top: `${top}%`,
              color: SPARKLE_COLORS[i % SPARKLE_COLORS.length],
              animationDelay: `${delay}s`,
              animationDuration: `${3.5 + (i % 4)}s`,
            }}
          >
            <Star size={size} />
          </span>
        ))}
      </Layer>
    </div>
  );
});
