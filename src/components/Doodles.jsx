import { memo } from "react";

// Hand-drawn doodles scattered around the hero. They're CSS masks filled with the muted ink color,
// so they follow the theme, and they float slowly in place. Offsets are relative to the hero grid.
const DOODLES = [
  // skyline sits like a horizon on top of the agent console (placed in the console's column)
  { src: "boston", group: "console", w: 489, h: 275, width: 270, style: { right: 12, top: 0 }, show: "lg", dur: 9, rot: 0 },
  // paper plane drifting in the gap between the name and the illustration
  { src: "plane", w: 570, h: 594, width: 92, style: { left: "calc(50% - 4rem)", top: -36 }, show: "lg", dur: 7, rot: 6, drift: true },
  // the rest live in the side margins, only where there's room
  { src: "book", w: 604, h: 474, width: 118, style: { left: -158, top: 40 }, show: "xl", dur: 8, rot: -6 },
  { src: "headphones", w: 610, h: 537, width: 104, style: { left: -150, top: 270 }, show: "xl", dur: 6.5, rot: 5 },
  { src: "laptop", w: 301, h: 225, width: 128, style: { right: -158, top: 340 }, show: "xl", dur: 8.5, rot: -4 },
];

// Margin doodles need roughly 150px of side margin, which only exists on wide screens.
const SHOW = { lg: "hidden lg:block", xl: "hidden min-[1380px]:block" };

// Values above are px at the default 16px root; convert to rem so doodles scale on big monitors.
const rem = (v) => (typeof v === "number" ? `${v / 16}rem` : v);
const toRem = (style) => Object.fromEntries(Object.entries(style).map(([k, v]) => [k, rem(v)]));

export const Doodles = memo(function Doodles({ group = "grid" }) {
  return (
    <div className="pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
      {DOODLES.filter((d) => (d.group || "grid") === group).map((d) => (
        <div
          key={d.src}
          className={`absolute ${SHOW[d.show]} ${d.drift ? "doodle-drift" : "doodle-float"}`}
          style={{ ...toRem(d.style), width: rem(d.width), aspectRatio: `${d.w} / ${d.h}`, "--rot": `${d.rot}deg`, animationDuration: `${d.dur}s` }}
        >
          <div
            className="h-full w-full bg-muted opacity-60"
            style={{
              WebkitMaskImage: `url(/doodles/${d.src}.png)`,
              maskImage: `url(/doodles/${d.src}.png)`,
              WebkitMaskSize: "contain",
              maskSize: "contain",
              WebkitMaskRepeat: "no-repeat",
              maskRepeat: "no-repeat",
            }}
          />
        </div>
      ))}
    </div>
  );
});
