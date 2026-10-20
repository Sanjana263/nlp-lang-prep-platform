import Link from "next/link";

/** Wordmark: a nine-step band ruler with the fifth step raised, beside the name. */
export function Brand({ href = "/", className = "" }: { href?: string; className?: string }) {
  return (
    <Link
      href={href}
      className={`inline-flex items-center gap-2.5 rounded-md text-ink focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-accent ${className}`}
    >
      <svg aria-hidden width="22" height="22" viewBox="0 0 22 22" className="text-accent">
        {Array.from({ length: 9 }, (_, i) => (
          <rect
            key={i}
            x={1 + i * 2.35}
            y={i === 6 ? 2 : 9}
            width="1.4"
            height={i === 6 ? 18 : 11}
            rx="0.7"
            fill="currentColor"
            opacity={i <= 6 ? 1 : 0.35}
          />
        ))}
      </svg>
      <span className="font-display text-[1.6rem] leading-none font-semibold tracking-tight">Cadence</span>
    </Link>
  );
}
