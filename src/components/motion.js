export const spring = { type: "spring", stiffness: 100, damping: 20 };

// Writes pointer coordinates to CSS variables for the .spotlight border (no React re-render).
export function trackSpotlight(e) {
  const r = e.currentTarget.getBoundingClientRect();
  e.currentTarget.style.setProperty("--mx", `${e.clientX - r.left}px`);
  e.currentTarget.style.setProperty("--my", `${e.clientY - r.top}px`);
}
