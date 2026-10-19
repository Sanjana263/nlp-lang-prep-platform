import { BookOpenTextIcon, HeadphonesIcon, MicrophoneIcon, PencilLineIcon } from "@phosphor-icons/react/ssr";
import type { ReactNode } from "react";
import { Brand } from "@/components/brand";
import { HomeCta } from "@/components/home-cta";
import { Badge, BandFigure, BandScale, Eyebrow, Panel } from "@/components/ui";

const SKILLS: { name: string; text: string; live: boolean; icon: ReactNode }[] = [
  { name: "Writing", text: "Task 2 essays scored on all four IELTS criteria, with feedback on what held the band back.", live: true, icon: <PencilLineIcon aria-hidden size={24} /> },
  { name: "Reading", text: "Timed passages with automatic scoring and a record of the question types you miss.", live: false, icon: <BookOpenTextIcon aria-hidden size={24} /> },
  { name: "Listening", text: "Clips in British, American and Australian accents, scored against the transcript.", live: false, icon: <HeadphonesIcon aria-hidden size={24} /> },
  { name: "Speaking", text: "Record an answer and get pronunciation, fluency and pace scores, plus a filler-word count.", live: false, icon: <MicrophoneIcon aria-hidden size={24} /> },
];

const STEPS = [
  { title: "Write to a real prompt", text: "Pick an IELTS Task 2 question and write as you would on the day: 40 minutes, at least 250 words." },
  { title: "We read it like an examiner", text: "Our language engine parses every sentence for grammar, structure, vocabulary range and task response." },
  { title: "Get a band and a reason", text: "You see an estimated band for each criterion, the overall band, and specific feedback to act on next." },
];

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <header className="border-b border-rule">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <Brand />
          <nav aria-label="Account" className="flex items-center gap-2">
            <HomeCta placement="nav" />
          </nav>
        </div>
      </header>

      <main id="main" className="flex-1">
        <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-14 sm:px-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,30rem)] lg:py-20">
          <div className="min-w-0">
            <Eyebrow>IELTS · TOEFL · PTE preparation</Eyebrow>
            <h1 className="mt-4 font-display text-5xl leading-[1.05] font-semibold tracking-tight text-ink sm:text-6xl">
              Know your band before exam day.
            </h1>
            <p className="mt-6 max-w-xl text-lg text-ink-2">
              Write an essay and get an estimated band in seconds, with the exact mistakes that are costing you marks.
              Practise all four skills and watch your scores move.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <HomeCta placement="hero" />
            </div>
          </div>
          <MarkedScript />
        </section>

        <section aria-labelledby="skills" className="border-y border-rule bg-surface">
          <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
            <h2 id="skills" className="font-display text-3xl font-semibold text-ink">All four skills, one score history</h2>
            <ul className="mt-8 grid gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-4">
              {SKILLS.map((s) => (
                <li key={s.name} className="grid content-start gap-3">
                  <div className="flex items-center justify-between">
                    <span className={s.live ? "text-accent" : "text-ink-3"}>{s.icon}</span>
                    {s.live ? <Badge tone="accent">Available</Badge> : <Badge>In development</Badge>}
                  </div>
                  <h3 className="text-lg font-semibold text-ink">{s.name}</h3>
                  <p className="text-ink-2">{s.text}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section aria-labelledby="how" className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
          <h2 id="how" className="font-display text-3xl font-semibold text-ink">How an essay gets its band</h2>
          <ol className="mt-8 grid gap-8 md:grid-cols-3">
            {STEPS.map((step, i) => (
              <li key={step.title} className="grid content-start gap-2 border-t-2 border-ink pt-4">
                <span className="font-mono text-sm text-ink-3 tabular-nums">Step {i + 1}</span>
                <h3 className="text-lg font-semibold text-ink">{step.title}</h3>
                <p className="text-ink-2">{step.text}</p>
              </li>
            ))}
          </ol>
        </section>
      </main>

      <footer className="border-t border-rule">
        <div className="mx-auto flex max-w-6xl flex-wrap justify-between gap-4 px-4 py-6 text-sm text-ink-3 sm:px-6">
          <p>Scores are automated estimates for practice, not official exam results.</p>
        </div>
      </footer>
    </div>
  );
}

/** A specimen of what the product returns: an essay excerpt marked up like an examiner would. */
function MarkedScript() {
  return (
    <Panel as="article" className="min-w-0 overflow-hidden shadow-[0_1px_0_var(--rule),0_24px_48px_-24px_rgb(18_26_43/0.25)]">
      <div className="flex items-center justify-between gap-3 border-b border-rule px-5 py-3">
        <Eyebrow>Writing Task 2 · marked</Eyebrow>
        <Badge>Example</Badge>
      </div>
      <div className="grid gap-4 px-5 py-5 sm:grid-cols-[minmax(0,1fr)_8.5rem]">
        <p className="font-display text-lg leading-8 text-ink">
          Some people{" "}
          <mark className="bg-transparent text-inherit underline decoration-red-pen decoration-wavy decoration-2 underline-offset-4">
            believes
          </mark>{" "}
          that university education should be free.{" "}
          <mark className="rounded-sm bg-accent-soft px-0.5 text-inherit">
            Although this would cost the government more, it would give poor students the same chance
          </mark>{" "}
          as everyone else.
        </p>
        <ul className="grid content-start gap-3 text-sm sm:border-l sm:border-rule sm:pl-4">
          <li>
            <span className="font-semibold text-red-pen">Subject–verb agreement</span>
            <span className="block text-ink-3">people believe</span>
          </li>
          <li>
            <span className="font-semibold text-accent">Complex sentence</span>
            <span className="block text-ink-3">raises grammatical range</span>
          </li>
        </ul>
      </div>
      <div className="grid gap-5 border-t border-rule bg-paper px-5 py-5 sm:grid-cols-[auto_minmax(0,1fr)] sm:items-end">
        <BandFigure score={6.5} />
        <BandScale score={6.5} label="Overall band" />
      </div>
    </Panel>
  );
}
