import { education, skills } from "../data";
import { Item, Reveal, Section } from "./Section";

export function Skills() {
  return (
    <Section id="skills" index="04" title="Skills & Education">
      <Reveal stagger={0.06} className="divide-y divide-line border-y border-line">
        {skills.map((s) => (
          <Item key={s.id} id={s.id} className="grid grid-cols-1 gap-3 px-1 py-6 md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] md:gap-12 md:px-4">
            <h3 className="font-mono text-xs tracking-wider text-muted uppercase">{s.group}</h3>
            <p className="leading-loose">
              {s.items.map((item, i) => (
                <span key={item}>
                  {item}
                  {i < s.items.length - 1 && <span className="mx-2 text-accent">/</span>}{" "}
                </span>
              ))}
            </p>
          </Item>
        ))}
      </Reveal>

      {/* No card boxes: two columns separated by a rule. */}
      <Reveal stagger={0.1} className="mt-12 grid gap-10 md:grid-cols-2 md:gap-0 md:divide-x md:divide-line">
        {education.map((e, i) => (
          <Item key={e.id} id={e.id} className={`p-1 md:p-4 ${i ? "md:pl-12" : "md:pr-12"}`}>
            <p className="font-mono text-xs text-muted">
              {e.period} · {e.location}
            </p>
            <h3 className="mt-3 text-2xl font-semibold tracking-tight">{e.school}</h3>
            <p className="mt-1 text-sm font-medium">{e.degree}</p>
            <p className="mt-3 text-sm leading-relaxed text-muted">{e.detail}</p>
          </Item>
        ))}
      </Reveal>
    </Section>
  );
}
