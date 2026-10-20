import { formatBand } from "@/lib/bands";

const GRID = [9, 6, 3, 0];

/**
 * Band history as a line on the fixed 0–9 scale (never auto-scaled, so a 6 always sits in the same place).
 * `points` are chronological, oldest first.
 */
export function BandTrend({ points }: { points: { band: number; date: string }[] }) {
  const n = points.length;
  const x = (i: number) => (n === 1 ? 50 : (i / (n - 1)) * 100);
  const y = (band: number) => 100 - (band / 9) * 100;
  const line = points.map((p, i) => `${x(i)},${y(p.band)}`).join(" ");
  const last = points[n - 1];
  const first = points[0];

  return (
    <figure className="grid gap-2">
      <div className="relative h-36 pl-7">
        {GRID.map((g) => (
          <div key={g} aria-hidden className="absolute inset-x-0 flex items-center gap-2" style={{ top: `${y(g)}%` }}>
            <span className="w-5 -translate-y-1/2 text-right font-mono text-[11px] text-ink-3 tabular-nums">{g}</span>
            <span className="h-px flex-1 -translate-y-1/2 bg-rule" />
          </div>
        ))}
        <div className="absolute inset-y-0 right-2 left-9">
          <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 size-full overflow-visible" aria-hidden>
            <polygon points={`${x(0)},100 ${line} ${x(n - 1)},100`} fill="var(--accent-soft)" opacity="0.7" />
            <polyline points={line} fill="none" stroke="var(--accent)" strokeWidth="2" vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
          </svg>
          <span
            aria-hidden
            className="absolute size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-surface bg-accent"
            style={{ left: `${x(n - 1)}%`, top: `${y(last.band)}%` }}
          />
        </div>
      </div>
      <figcaption className="text-sm text-ink-3">
        Writing band over your last {n} essays, from {formatBand(first.band)} ({first.date}) to{" "}
        <span className="font-semibold text-ink">{formatBand(last.band)}</span> ({last.date}).
      </figcaption>
    </figure>
  );
}
