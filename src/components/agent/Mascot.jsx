import { memo, useEffect, useId } from "react";
import { motion, useMotionValue, useReducedMotion, useSpring } from "framer-motion";
import { MASCOT_NAME } from "./mascotMood";

const float = {
  idle: { y: [0, -4, 0], rotate: 0, scaleX: 1, scaleY: 1, transition: { y: { duration: 3.2, repeat: Infinity, ease: "easeInOut" } } },
  sleepy: { y: [0, 1.5, 0], rotate: -4, scaleX: 1.03, scaleY: 0.97, transition: { y: { duration: 4, repeat: Infinity, ease: "easeInOut" } } },
  thinking: { y: [0, -3, 0], rotate: [0, 3, -3, 0], transition: { duration: 1.6, repeat: Infinity, ease: "easeInOut" } },
  talking: { y: 0, scaleX: [1, 1.04, 1], scaleY: [1, 0.96, 1], rotate: 0, transition: { duration: 0.42, repeat: Infinity, ease: "easeInOut" } },
  happy: { y: [0, -9, 0], rotate: 0, scaleX: 1, scaleY: 1, transition: { y: { type: "spring", stiffness: 300, damping: 10, repeat: Infinity, repeatDelay: 0.5 } } },
  unsure: { y: 0, rotate: -9, scaleX: 1, scaleY: 1, transition: { type: "spring", stiffness: 120, damping: 12 } },
};

function Eyes({ mood }) {
  if (mood === "happy") {
    const heart = (cx) => `M${cx} 61.5c-2.6-1.9-5.2-3.9-5.2-6.4 0-1.6 1.2-2.8 2.7-2.8 1 0 1.9.5 2.5 1.4.6-.9 1.5-1.4 2.5-1.4 1.5 0 2.7 1.2 2.7 2.8 0 2.5-2.6 4.5-5.2 6.4z`;
    return (
      <g fill="#ff7eb3">
        <path d={heart(50)} />
        <path d={heart(74)} />
      </g>
    );
  }
  if (mood === "sleepy") {
    return (
      <g fill="none" stroke="#2a2638" strokeWidth="2" strokeLinecap="round">
        <path d="M45.5 57.5q4.5 3.2 9 0" />
        <path d="M69.5 57.5q4.5 3.2 9 0" />
      </g>
    );
  }
  return (
    <g className="mascot-eyes">
      {[50, 74].map((cx) => (
        <g key={cx}>
          <ellipse cx={cx} cy={57} rx={4.2} ry={5.2} fill="#2a2638" />
          <circle cx={cx + 1.5} cy={54.8} r={1.6} fill="#fff" />
          <path d={`M${cx - 1.8} 59.2l.5 1 1 .4-1 .4-.5 1-.5-1-1-.4 1-.4z`} fill="#fff" opacity=".9" />
        </g>
      ))}
    </g>
  );
}

function Mouth({ mood, reduce }) {
  if (mood === "talking" && !reduce) {
    return (
      <motion.ellipse
        cx={62}
        cy={67.5}
        rx={3.4}
        fill="#2a2638"
        animate={{ ry: [1.2, 3.2, 1.6, 2.8, 1.2] }}
        transition={{ duration: 0.6, repeat: Infinity }}
      />
    );
  }
  const d = {
    unsure: "M57.5 68.5q2.2-1.6 4.5 0t4.5 0",
    sleepy: "M60 67.5q2 1.4 4 0",
    thinking: "M59.5 67.5h5",
    happy: "M56.5 65.5q5.5 6 11 0",
  }[mood] || "M57.5 66q4.5 4 9 0";
  return <path d={d} fill="none" stroke="#2a2638" strokeWidth="2" strokeLinecap="round" />;
}

// A soft cloud with sparkly eyes. `track` makes the eyes follow the cursor (use on the big one only).
export const Mascot = memo(function Mascot({ mood = "idle", size = 64, track = false, still = false, className = "" }) {
  const reduce = useReducedMotion();
  const gid = useId().replace(/:/g, "");
  const ex = useMotionValue(0);
  const ey = useMotionValue(0);
  const sx = useSpring(ex, { stiffness: 120, damping: 14 });
  const sy = useSpring(ey, { stiffness: 120, damping: 14 });

  useEffect(() => {
    if (!track || reduce) return;
    const onMove = (e) => {
      ex.set(Math.max(-1, Math.min(1, (e.clientX / window.innerWidth - 0.5) * 2)) * 2.2);
      ey.set(Math.max(-1, Math.min(1, (e.clientY / window.innerHeight - 0.5) * 2)) * 1.6);
    };
    window.addEventListener("pointermove", onMove, { passive: true });
    return () => window.removeEventListener("pointermove", onMove);
  }, [track, reduce, ex, ey]);

  useEffect(() => {
    if (mood === "thinking") {
      ex.set(1.2);
      ey.set(-2.4); // look up while thinking
    } else if (!track) {
      ex.set(0);
      ey.set(0);
    }
  }, [mood, track, ex, ey]);

  return (
    <motion.svg
      viewBox="0 0 124 100"
      width={size}
      height={(size * 100) / 124}
      className={`overflow-visible ${className}`}
      animate={reduce || still ? undefined : float[mood] || float.idle}
      style={{ originY: 1 }}
      role="img"
      aria-label={`${MASCOT_NAME}, feeling ${mood}`}
    >
      <defs>
        <linearGradient id={`body-${gid}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="var(--mascot-top)" />
          <stop offset="1" stopColor="var(--mascot-bottom)" />
        </linearGradient>
      </defs>

      <ellipse cx="62" cy="94" rx="30" ry="3.5" fill="var(--accent)" opacity=".14" />

      {/* cloud body */}
      <g fill={`url(#body-${gid})`} stroke="var(--line)" strokeWidth="1.2">
        <path d="M30 84c-11 0-19-8-19-18 0-9.5 7-17 16.5-18C29 35 39 26 51 27c5-9 14-14 24-13 13 1 23 11 24 24 9 2 15 10 15 19 0 15-11 27-26 27z" />
      </g>
      <path d="M40 40c4-6 10-9 16-9" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" opacity=".8" />

      {/* face */}
      <motion.g style={{ x: sx, y: sy }}>
        <Eyes mood={mood} />
        <Mouth mood={mood} reduce={reduce} />
        <ellipse cx="41.5" cy="65" rx="5" ry="3" fill="#ffb3d1" opacity=".75" />
        <ellipse cx="82.5" cy="65" rx="5" ry="3" fill="#ffb3d1" opacity=".75" />
      </motion.g>

      {mood === "thinking" && !reduce && (
        <motion.g
          animate={{ rotate: 360 }}
          transition={{ duration: 2.4, repeat: Infinity, ease: "linear" }}
          style={{ originX: "62px", originY: "52px" }}
          fill="var(--accent)"
        >
          {[0, 120, 240].map((a) => (
            <path
              key={a}
              transform={`rotate(${a} 62 52) translate(62 4)`}
              d="M0-4c.3 2.6 1.4 3.7 4 4-2.6.3-3.7 1.4-4 4-.3-2.6-1.4-3.7-4-4 2.6-.3 3.7-1.4 4-4z"
            />
          ))}
        </motion.g>
      )}

      {mood === "sleepy" &&
        [0, 0.8, 1.6].map((d, i) => (
          <text
            key={i}
            x={100 + i * 5}
            y={30 - i * 6}
            className="mascot-z"
            style={{ animationDelay: `${d}s` }}
            fontSize={9 + i * 2}
            fontWeight="600"
            fill="var(--accent)"
          >
            z
          </text>
        ))}

      {mood === "unsure" && (
        <text x="102" y="32" fontSize="16" fontWeight="700" fill="var(--accent)">
          ?
        </text>
      )}
    </motion.svg>
  );
});
