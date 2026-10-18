import { HomeCta } from "@/components/home-cta";

const skills = [
  { name: "Writing", text: "Instant band estimate and feedback on your essays.", live: true },
  { name: "Reading", text: "Timed passages with automatic scoring.", live: false },
  { name: "Listening", text: "Clips in British, American and Australian accents.", live: false },
  { name: "Speaking", text: "Record answers and get pronunciation and fluency scores.", live: false },
];

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col justify-center px-6 py-20">
      <p className="text-sm font-medium text-indigo-600 dark:text-indigo-400">Cadence</p>
      <h1 className="mt-3 max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl">
        Prepare for IELTS, TOEFL and PTE with instant AI feedback.
      </h1>
      <p className="mt-5 max-w-xl text-lg leading-8 text-zinc-600 dark:text-zinc-400">
        Practise all four skills in one place, see exactly where you lose marks, and track your progress over time.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <HomeCta />
      </div>

      <div className="mt-16 grid gap-4 sm:grid-cols-2">
        {skills.map((s) => (
          <div key={s.name} className="rounded-2xl border border-zinc-200 p-5 dark:border-zinc-800">
            <div className="flex items-center justify-between">
              <h2 className="font-medium">{s.name}</h2>
              {!s.live && (
                <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
                  Coming soon
                </span>
              )}
            </div>
            <p className="mt-1.5 text-sm text-zinc-600 dark:text-zinc-400">{s.text}</p>
          </div>
        ))}
      </div>
      <p className="mt-10 text-xs text-zinc-500">
        Scores are automated estimates for practice only, not official exam results.
      </p>
    </main>
  );
}
