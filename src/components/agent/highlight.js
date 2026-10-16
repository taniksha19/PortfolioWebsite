// Links agent citations back to the page: scroll-and-flash one section, or glow several.
// Write-up citations look like "proj-break-the-bot--pipeline" and point at their project's card.
export const sectionOf = (id) => id.split("--")[0];

export function flashSection(id) {
  const el = document.getElementById(sectionOf(id));
  if (!el) return;
  el.scrollIntoView({ behavior: "smooth", block: "center" });
  el.classList.remove("cite-flash");
  void el.offsetWidth; // restart the animation
  el.classList.add("cite-flash");
  setTimeout(() => el.classList.remove("cite-flash"), 2200);
}

export function glowSections(ids) {
  clearGlow();
  new Set(ids.map(sectionOf)).forEach((id) => document.getElementById(id)?.classList.add("fit-glow"));
}

export function clearGlow() {
  document.querySelectorAll(".fit-glow").forEach((el) => el.classList.remove("fit-glow"));
}
