// Cadence UI kit. Every page builds from these instead of styling elements ad hoc.
// Server-safe (no hooks), so it works in Server and Client Components alike.
import Link from "next/link";
import type {
  ButtonHTMLAttributes,
  ComponentProps,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
} from "react";
import { CaretDownIcon, CheckCircleIcon, InfoIcon, WarningCircleIcon } from "@phosphor-icons/react/ssr";
import { bandDescriptor, bandFill, bandTone, formatBand } from "@/lib/bands";

const cx = (...parts: (string | false | null | undefined)[]) => parts.filter(Boolean).join(" ");

/* ---------- Buttons ---------- */

type Variant = "primary" | "secondary" | "ghost";
type Size = "md" | "sm";

const focusRing =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent";

export function buttonClass(variant: Variant = "primary", size: Size = "md", className?: string) {
  return cx(
    "inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg font-semibold whitespace-nowrap",
    "transition-colors duration-150 ease-out touch-manipulation select-none",
    "disabled:cursor-not-allowed disabled:opacity-45",
    focusRing,
    size === "md" ? "min-h-11 px-5 text-[15px]" : "min-h-9 px-3.5 text-sm",
    variant === "primary" && "bg-accent text-on-accent hover:bg-accent-hover",
    variant === "secondary" && "border border-rule-strong bg-surface text-ink hover:bg-surface-2",
    variant === "ghost" && "text-ink-2 hover:bg-surface-2 hover:text-ink",
    className,
  );
}

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  className,
  children,
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: Size; loading?: boolean }) {
  return (
    <button
      className={buttonClass(variant, size, className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && <Spinner />}
      {children}
    </button>
  );
}

export function LinkButton({
  variant = "primary",
  size = "md",
  className,
  ...props
}: ComponentProps<typeof Link> & { variant?: Variant; size?: Size }) {
  return <Link className={buttonClass(variant, size, className)} {...props} />;
}

export function TextLink({ className, ...props }: ComponentProps<typeof Link>) {
  return (
    <Link
      className={cx("rounded-sm font-semibold text-accent underline-offset-4 hover:underline", focusRing, className)}
      {...props}
    />
  );
}

/* ---------- Form fields ---------- */

export const inputClass = cx(
  "block w-full min-h-11 rounded-lg border border-rule-strong bg-surface px-3.5 text-base text-ink",
  "placeholder:text-ink-3 transition-colors duration-150",
  "focus:border-accent focus:outline-none focus:ring-3 focus:ring-accent/25",
  "aria-[invalid=true]:border-red-pen aria-[invalid=true]:ring-red-pen/20",
  "disabled:cursor-not-allowed disabled:bg-surface-2 disabled:text-ink-2",
);

type FieldExtras = { label: string; id: string; hint?: string; error?: string | null };

function FieldShell({ id, label, hint, error, children }: FieldExtras & { children: ReactNode }) {
  return (
    <div className="grid gap-1.5">
      <label htmlFor={id} className="text-sm font-semibold text-ink">
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} className="flex items-center gap-1.5 text-sm text-red-pen">
          <WarningCircleIcon aria-hidden size={16} weight="bold" />
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${id}-hint`} className="text-sm text-ink-3">
            {hint}
          </p>
        )
      )}
    </div>
  );
}

export function describedBy(id: string, hint?: string, error?: string | null) {
  return error ? `${id}-error` : hint ? `${id}-hint` : undefined;
}

export function Field({ label, id, hint, error, className, ...props }: InputHTMLAttributes<HTMLInputElement> & FieldExtras) {
  return (
    <FieldShell id={id} label={label} hint={hint} error={error}>
      <input
        id={id}
        className={cx(inputClass, className)}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, hint, error)}
        {...props}
      />
    </FieldShell>
  );
}

export function SelectField({
  label,
  id,
  hint,
  error,
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & FieldExtras) {
  return (
    <FieldShell id={id} label={label} hint={hint} error={error}>
      <div className="relative">
        <select
          id={id}
          className={cx(inputClass, "cursor-pointer appearance-none pr-10")}
          aria-describedby={describedBy(id, hint, error)}
          {...props}
        >
          {children}
        </select>
        <CaretDownIcon
          aria-hidden
          size={16}
          weight="bold"
          className="pointer-events-none absolute top-1/2 right-3.5 -translate-y-1/2 text-ink-3"
        />
      </div>
    </FieldShell>
  );
}

/* ---------- Surfaces and feedback ---------- */

/** A bordered surface. Use for objects that stand apart (a form, a result), not for every block. */
export function Panel({ children, className, as: Tag = "div" }: { children: ReactNode; className?: string; as?: "div" | "section" | "article" }) {
  return <Tag className={cx("rounded-xl border border-rule bg-surface", className)}>{children}</Tag>;
}

const ALERT = {
  error: { cls: "border-red-pen/30 bg-red-soft text-red-pen", Icon: WarningCircleIcon, role: "alert" },
  success: { cls: "border-success/30 bg-surface text-success", Icon: CheckCircleIcon, role: "status" },
  info: { cls: "border-rule bg-surface-2 text-ink-2", Icon: InfoIcon, role: "status" },
} as const;

export function Alert({ tone = "error", children }: { tone?: keyof typeof ALERT; children: ReactNode }) {
  const { cls, Icon, role } = ALERT[tone];
  return (
    <div role={role} className={cx("flex items-start gap-2.5 rounded-lg border px-3.5 py-3 text-sm", cls)}>
      <Icon aria-hidden size={18} weight="bold" className="mt-0.5 shrink-0" />
      <div className="min-w-0">{children}</div>
    </div>
  );
}

/** Kept for existing call sites. */
export const ErrorAlert = ({ children }: { children: ReactNode }) => <Alert tone="error">{children}</Alert>;

export function Badge({ tone = "neutral", children }: { tone?: "neutral" | "accent" | "danger"; children: ReactNode }) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-md px-2 py-0.5 font-mono text-xs font-medium tracking-wide uppercase",
        tone === "neutral" && "bg-surface-2 text-ink-2",
        tone === "accent" && "bg-accent-soft text-accent",
        tone === "danger" && "bg-red-soft text-red-pen",
      )}
    >
      {children}
    </span>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      aria-hidden
      className={cx("inline-block size-4 animate-spin rounded-full border-2 border-current border-t-transparent", className)}
    />
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cx("animate-pulse rounded-md bg-surface-2", className)} />;
}

/** Small uppercase label used above headings and data. */
export function Eyebrow({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cx("font-mono text-xs font-medium tracking-[0.12em] text-ink-3 uppercase", className)}>{children}</p>;
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-x-8 gap-y-4">
      <div className="min-w-0 max-w-2xl">
        {eyebrow && <Eyebrow className="mb-2">{eyebrow}</Eyebrow>}
        <h1 className="font-display text-4xl leading-tight font-semibold tracking-tight text-ink sm:text-[2.75rem]">
          {title}
        </h1>
        {description && <p className="mt-2 text-ink-2">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-3">{actions}</div>}
    </header>
  );
}

export function SectionHeading({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="mb-4 flex items-baseline justify-between gap-4">
      <h2 className="font-display text-2xl font-semibold text-ink">{children}</h2>
      {action}
    </div>
  );
}

export function EmptyState({ icon, title, children, action }: { icon?: ReactNode; title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="grid justify-items-center gap-3 rounded-xl border border-dashed border-rule-strong px-6 py-10 text-center">
      {icon && <div className="text-ink-3">{icon}</div>}
      <p className="font-semibold text-ink">{title}</p>
      {children && <p className="max-w-sm text-sm text-ink-2">{children}</p>}
      {action && <div className="mt-1">{action}</div>}
    </div>
  );
}

/* ---------- Band score devices ---------- */

/**
 * The 0–9 band ruler: the platform's signature element. One tick per band,
 * a filled track up to the score and a marker on it. Always shows the number too.
 */
export function BandScale({ score, size = "md", label }: { score: number | null; size?: "sm" | "md"; label?: string }) {
  const pct = score === null ? 0 : (score / 9) * 100;
  return (
    <div
      role="img"
      aria-label={score === null ? `${label ?? "Band"}: no score yet` : `${label ?? "Band"} ${formatBand(score)} of 9`}
      className="w-full"
    >
      <div className={cx("relative rounded-full bg-surface-2", size === "md" ? "h-2" : "h-1.5")}>
        {score !== null && (
          <>
            <div className={cx("absolute inset-y-0 left-0 rounded-full", bandFill(score))} style={{ width: `${pct}%` }} />
            <div
              className={cx(
                "absolute top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-surface",
                bandFill(score),
                size === "md" ? "size-4" : "size-3",
              )}
              style={{ left: `${pct}%` }}
            />
          </>
        )}
      </div>
      {size === "md" && (
        <div aria-hidden className="mt-2 flex justify-between font-mono text-[11px] text-ink-3 tabular-nums">
          {Array.from({ length: 10 }, (_, i) => (
            <span key={i} className="w-3 text-center">
              {i}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/** Large band numeral with its IELTS descriptor underneath. */
export function BandFigure({ score, size = "lg" }: { score: number | null; size?: "lg" | "xl" }) {
  return (
    <div>
      <p
        className={cx(
          "font-display leading-none font-semibold tabular-nums",
          size === "xl" ? "text-7xl sm:text-8xl" : "text-5xl",
          score === null ? "text-ink-3" : bandTone(score),
        )}
      >
        {formatBand(score)}
      </p>
      <p className="mt-2 text-sm font-semibold text-ink-2">{score === null ? "No score yet" : bandDescriptor(score)}</p>
    </div>
  );
}
