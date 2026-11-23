import { ArrowRightIcon } from "@phosphor-icons/react";
import { Item, Reveal } from "./Section";

// A window into fun mode: a Blender still of the room (day in light theme, night in dark) that opens it.
export function RoomPeek({ onFun }) {
  if (!onFun) return null;
  return (
    <section aria-labelledby="peek-title" className="mx-auto max-w-6xl px-4 py-12 sm:px-6 md:py-16">
      <Reveal
        stagger={0.08}
        className="grid items-center gap-8 rounded-[2rem] border border-line bg-surface p-3 shadow-[var(--shadow)] md:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] md:gap-10 md:p-4"
      >
        <Item>
          <button
            onClick={onFun}
            className="peek group relative block w-full overflow-hidden rounded-[1.5rem] active:scale-[0.99]"
            aria-label="Open the 3D room"
          >
            <img
              src="/desk/peek-day.webp"
              alt="My 3D room on a sunny afternoon: a white desk with a laptop, a cork board, lilies and a cloud on the windowsill"
              width="1200"
              height="750"
              loading="lazy"
              className="peek-day block aspect-[16/10] w-full object-cover transition-transform duration-700 group-hover:scale-[1.03]"
            />
            <img
              src="/desk/peek-night.webp"
              alt="My 3D room at night: the desk lamp glowing and fairy lights over the window"
              width="1200"
              height="750"
              loading="lazy"
              className="peek-night block aspect-[16/10] w-full object-cover transition-transform duration-700 group-hover:scale-[1.03]"
            />
            <span className="absolute bottom-3 left-3 rounded-full bg-bg/85 px-3 py-1.5 font-mono text-xs text-ink backdrop-blur-sm">
              rendered in Blender
            </span>
          </button>
        </Item>
        <div className="px-3 pb-5 md:px-0 md:pb-0 md:pr-6">
          <Item as="p" className="font-mono text-xs text-accent">
            psst, there&rsquo;s another version of this site
          </Item>
          <Item as="h2" id="peek-title" className="mt-3 text-balance text-3xl font-semibold leading-tight tracking-tight md:text-4xl">
            Come hang out in my room
          </Item>
          <Item as="p" className="mt-4 max-w-[42ch] leading-relaxed text-muted">
            Same story, told through the things on my desk. Click the clipboard for my résumé, the record player for
            my experience, or the little cloud on the windowsill to chat with Nimbus.
          </Item>
          <Item className="mt-7">
            <button
              onClick={onFun}
              className="group inline-flex items-center gap-2 rounded-full bg-accent px-6 py-3 text-sm font-semibold text-bg transition-all hover:opacity-90 active:scale-[0.98]"
            >
              Make it fun ✨
              <ArrowRightIcon size={16} className="transition-transform group-hover:translate-x-0.5" />
            </button>
          </Item>
        </div>
      </Reveal>
    </section>
  );
}
