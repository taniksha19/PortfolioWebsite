// Shapes content/portfolio.json into what the fun-mode room renders, so both modes share one source.
import { profile, experience, projects, skills } from "../data";

// Short labels for the app icons on the laptop screen.
const ICONS = [
  [/break the bot/i, "▶"],
  [/detox/i, "Dx"],
  [/stack overflow/i, "SO"],
  [/spotify/i, "♫"],
  [/freelancer/i, "FC"],
  [/image transformer/i, "IT"],
  [/test drive/i, "TD"],
];
const initials = (title) =>
  title
    .split(/[\s–-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");

export const roomData = {
  profile,
  resume: profile.resume,
  projects: projects.map((p) => ({
    t: p.title,
    k: p.kind,
    s: p.summary,
    p: p.points,
    st: p.stack,
    link: p.link,
    game: /break the bot/i.test(p.title),
    ab: (ICONS.find(([re]) => re.test(p.title)) || [])[1] || initials(p.title),
  })),
  jobs: experience.map((j) => ({ t: j.role, c: j.company, d: j.period, p: j.points })),
  skills: Object.fromEntries(skills.map((g) => [g.group, g.items.join(", ")])),
};
