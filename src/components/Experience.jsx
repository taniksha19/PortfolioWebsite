import { experience } from "../data";
import { Item, Reveal, Section, Tag } from "./Section";

export function Experience() {
  return (
    <Section
      id="experience"
      index="01"
      title="Experience"
      kicker="Most recently: agent systems in production at Bevi, from retrieval and MCP tooling to the evals that gate each release."
    >
      <ol className="divide-y divide-line border-y border-line">
        {experience.map((job) => (
          <Reveal
            as="li"
            id={job.id}
            key={job.id}
            stagger={0.06}
            className="grid gap-4 px-1 py-8 md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] md:gap-12 md:px-4"
          >
            <Item>
              <h3 className="text-2xl font-semibold tracking-tight">{job.company}</h3>
              <p className="mt-1 text-muted">{job.role}</p>
              <p className="mt-4 font-mono text-xs leading-6 text-muted">
                {job.period}
                <br />
                {job.location}
              </p>
            </Item>
            <div>
              <ul className="space-y-3">
                {job.points.map((p) => (
                  <Item as="li" key={p} className="relative max-w-[70ch] pl-5 leading-relaxed text-muted">
                    <span className="absolute top-[0.75em] left-0 h-px w-2.5 bg-accent" />
                    {p}
                  </Item>
                ))}
              </ul>
              <Item className="mt-6 flex flex-wrap gap-2">
                {job.tags.map((t) => (
                  <Tag key={t}>{t}</Tag>
                ))}
              </Item>
            </div>
          </Reveal>
        ))}
      </ol>
    </Section>
  );
}
