import { memo, useEffect, useState } from "react";
import { AnimatePresence, motion, useMotionValue, useReducedMotion, useSpring, useTransform } from "framer-motion";
import { Mascot } from "./agent/Mascot";
import { spring } from "./motion";

// Coordinates are in the illustration's own pixels (426 × 687), so the overlay scales with the image.
const EYES = [
  { cx: 133, cy: 247, rx: 51, ry: 42, tilt: 4 },
  { cx: 294, cy: 227, rx: 49, ry: 41, tilt: -6 },
];
const LENSES = [
  { cx: 127, cy: 250, rx: 62, ry: 50 },
  { cx: 292, cy: 225, rx: 64, ry: 52 },
];
const SKIN = "#fbc9a2";

// The illustration is a single flat image, so the whole figure breathes, sways and leans toward the
// cursor; blinks and a glasses glint are drawn on top in SVG.
export const MeAndNimbus = memo(function MeAndNimbus({ className = "" }) {
  const reduce = useReducedMotion();
  const [hover, setHover] = useState(false);
  const mx = useMotionValue(0);
  const lean = useSpring(useTransform(mx, (v) => v * 2.5), { stiffness: 60, damping: 14 });

  useEffect(() => {
    if (reduce) return;
    const onMove = (e) => mx.set(e.clientX / window.innerWidth - 0.5);
    window.addEventListener("pointermove", onMove, { passive: true });
    return () => window.removeEventListener("pointermove", onMove);
  }, [reduce, mx]);

  return (
    <div
      className={`relative select-none ${className}`}
      onPointerEnter={() => setHover(true)}
      onPointerLeave={() => setHover(false)}
    >
      {/* Nimbus floats by her shoulder and gets excited when she's hovered */}
      <div className="absolute -top-2 -right-16 z-10 sm:-right-20 lg:-top-20 lg:right-0">
        <Mascot mood={hover ? "happy" : "idle"} size={88} track />
      </div>

      <AnimatePresence>
        {hover && (
          <motion.p
            initial={{ opacity: 0, y: 6, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 6, scale: 0.9 }}
            transition={spring}
            className="absolute -top-10 left-1/2 z-10 -translate-x-1/2 rounded-2xl rounded-bl-md lg:left-0 lg:-translate-x-[35%] border border-line bg-surface px-3 py-1.5 text-sm font-medium whitespace-nowrap shadow-[var(--shadow)]"
          >
            Hi, I&rsquo;m Taniksha!
          </motion.p>
        )}
      </AnimatePresence>

      <motion.div style={{ rotate: reduce ? 0 : lean, originX: 0.5, originY: 1 }}>
        <motion.div
          animate={
            reduce
              ? undefined
              : hover
                ? { y: [0, -14, 0], scaleY: [1, 1.02, 1], transition: { duration: 0.5, ease: "easeOut" } }
                : { scaleY: [1, 1.012, 1], rotate: [-0.6, 0.6, -0.6], transition: { duration: 4.2, repeat: Infinity, ease: "easeInOut" } }
          }
          style={{ originX: 0.5, originY: 1 }}
          className="relative"
        >
          <picture>
            <source srcSet="/taniksha.webp" type="image/webp" />
            <img
              src="/taniksha.png"
              alt="Illustration of Taniksha in glasses, a navy top and black jeans"
              width={426}
              height={687}
              draggable={false}
              className="block h-auto w-full drop-shadow-[0_18px_22px_rgba(115,87,201,0.18)]"
            />
          </picture>

          <svg viewBox="0 0 426 687" className="pointer-events-none absolute inset-0 h-full w-full" aria-hidden="true">
            <defs>
              <clipPath id="me-lenses">
                {LENSES.map((l, i) => (
                  <ellipse key={i} {...l} />
                ))}
              </clipPath>
              <linearGradient id="me-glint" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0" stopColor="#fff" stopOpacity="0" />
                <stop offset=".5" stopColor="#fff" stopOpacity=".75" />
                <stop offset="1" stopColor="#fff" stopOpacity="0" />
              </linearGradient>
            </defs>

            {!reduce && (
              <>
                {/* closed eyelids, shown for a split second on each blink */}
                <g className="me-blink">
                  {EYES.map((e, i) => (
                    <g key={i} transform={`rotate(${e.tilt} ${e.cx} ${e.cy})`}>
                      <ellipse cx={e.cx} cy={e.cy} rx={e.rx} ry={e.ry} fill={SKIN} />
                      <path
                        d={`M${e.cx - e.rx * 0.9} ${e.cy + 4} Q${e.cx} ${e.cy + e.ry * 0.62} ${e.cx + e.rx * 0.9} ${e.cy + 4}`}
                        fill="none"
                        stroke="#2b211c"
                        strokeWidth="5"
                        strokeLinecap="round"
                      />
                      {[-0.55, -0.15, 0.25, 0.62].map((t) => (
                        <path
                          key={t}
                          d={`M${e.cx + e.rx * t} ${e.cy + e.ry * 0.36} l${t * 5} 12`}
                          stroke="#2b211c"
                          strokeWidth="3.5"
                          strokeLinecap="round"
                        />
                      ))}
                    </g>
                  ))}
                </g>

                {/* a soft glint sweeping across the lenses */}
                <g clipPath="url(#me-lenses)">
                  <rect className="me-glint" x="-140" y="150" width="70" height="200" fill="url(#me-glint)" transform="skewX(-20)" />
                </g>
              </>
            )}
          </svg>
        </motion.div>
      </motion.div>

      <div className="mx-auto -mt-2 h-3 w-3/5 rounded-[100%] bg-accent opacity-15 blur-[2px]" />
    </div>
  );
});
