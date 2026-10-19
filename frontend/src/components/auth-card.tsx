import type { ReactNode } from "react";
import { Brand } from "@/components/brand";

const DESCRIPTORS: [string, string][] = [
  ["9", "Expert user"],
  ["8", "Very good user"],
  ["7", "Good user"],
  ["6", "Competent user"],
  ["5", "Modest user"],
];

/** Two-column auth layout: form on the left, the band descriptor scale on the right (lg+). */
export function AuthCard({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="grid flex-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,28rem)]">
      <main id="main" className="flex flex-col px-4 py-8 sm:px-8">
        <Brand />
        <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center py-12">
          <h1 className="font-display text-4xl font-semibold tracking-tight text-ink">{title}</h1>
          <p className="mt-2 mb-8 text-ink-2">{subtitle}</p>
          {children}
        </div>
      </main>

      <aside className="hidden border-l border-rule bg-surface px-10 py-12 lg:flex lg:flex-col lg:justify-center">
        <p className="font-mono text-xs font-medium tracking-[0.12em] text-ink-3 uppercase">IELTS band descriptors</p>
        <ol className="mt-6 grid gap-1">
          {DESCRIPTORS.map(([band, name]) => (
            <li key={band} className="flex items-baseline gap-4 border-b border-rule py-3 text-ink-2">
              <span className="w-8 font-display text-3xl font-semibold text-ink tabular-nums">{band}</span>
              <span>{name}</span>
            </li>
          ))}
        </ol>
        <p className="mt-8 max-w-xs text-sm text-ink-2">
          Every essay you submit gets an estimated band on this scale, with the criteria that held it back.
        </p>
      </aside>
    </div>
  );
}
