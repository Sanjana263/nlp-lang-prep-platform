"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import {
  BookOpenTextIcon,
  CardsIcon,
  HeadphonesIcon,
  MicrophoneIcon,
  PencilLineIcon,
  SignOutIcon,
  SquaresFourIcon,
  UserCircleIcon,
} from "@phosphor-icons/react/ssr";
import { Brand } from "@/components/brand";
import { Spinner } from "@/components/ui";
import { useAuth } from "@/lib/auth";

const NAV = [
  { href: "/dashboard", label: "Dashboard", Icon: SquaresFourIcon },
  { href: "/writing", label: "Writing", Icon: PencilLineIcon },
  { href: "/settings", label: "Profile", Icon: UserCircleIcon },
];
// Shown, not hidden, so students know what is coming (and why they can't open it yet).
const IN_DEVELOPMENT = [
  { label: "Reading", Icon: BookOpenTextIcon },
  { label: "Listening", Icon: HeadphonesIcon },
  { label: "Speaking", Icon: MicrophoneIcon },
  { label: "Vocabulary", Icon: CardsIcon },
];

export default function AppLayout({ children }: { children: ReactNode }) {
  const { user, status, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  // NFR-1.3: everything inside this route group requires login.
  useEffect(() => {
    if (status === "anonymous") router.replace("/login");
  }, [status, router]);

  if (status !== "authenticated" || !user) {
    return (
      <div role="status" className="flex flex-1 items-center justify-center gap-3 text-ink-2">
        <Spinner /> Loading your workspace…
      </div>
    );
  }

  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);
  const initials = user.full_name
    .split(/\s+/)
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <div className="flex flex-1 flex-col md:flex-row">
      {/* Desktop / tablet sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-rule bg-surface md:flex">
        <div className="sticky top-0 flex h-dvh flex-col px-4 py-6">
          <Brand href="/dashboard" className="px-2" />

          <nav aria-label="Main" className="mt-10 grid gap-1">
            {NAV.map(({ href, label, Icon }) => (
              <Link
                key={href}
                href={href}
                aria-current={isActive(href) ? "page" : undefined}
                className="flex min-h-11 items-center gap-3 rounded-lg px-3 font-semibold text-ink-2 transition-colors duration-150 hover:bg-surface-2 hover:text-ink focus-visible:outline-2 focus-visible:outline-accent aria-[current=page]:bg-accent-soft aria-[current=page]:text-accent"
              >
                <Icon aria-hidden size={20} weight={isActive(href) ? "fill" : "regular"} />
                {label}
              </Link>
            ))}
          </nav>

          <div className="mt-8">
            <p className="px-3 font-mono text-[11px] font-medium tracking-[0.12em] text-ink-3 uppercase">In development</p>
            <ul className="mt-2 grid gap-0.5" aria-label="Skills in development">
              {IN_DEVELOPMENT.map(({ label, Icon }) => (
                <li key={label} className="flex min-h-9 items-center gap-3 px-3 text-ink-3">
                  <Icon aria-hidden size={20} />
                  {label}
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-auto border-t border-rule pt-4">
            <div className="flex items-center gap-3 px-2">
              <span aria-hidden className="grid size-9 shrink-0 place-items-center rounded-full bg-surface-2 text-sm font-semibold text-ink-2">
                {initials}
              </span>
              <div className="min-w-0">
                <p className="truncate font-semibold text-ink" title={user.full_name}>{user.full_name}</p>
                <p className="truncate text-sm text-ink-3" title={user.email}>{user.email}</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="mt-3 flex min-h-11 w-full cursor-pointer items-center gap-3 rounded-lg px-3 text-ink-2 transition-colors duration-150 hover:bg-surface-2 hover:text-ink focus-visible:outline-2 focus-visible:outline-accent"
            >
              <SignOutIcon aria-hidden size={20} /> Log out
            </button>
          </div>
        </div>
      </aside>

      {/* Phone top bar */}
      <header className="sticky top-0 z-20 flex items-center justify-between border-b border-rule bg-surface/95 px-4 py-3 backdrop-blur md:hidden">
        <Brand href="/dashboard" />
        <button
          onClick={logout}
          aria-label="Log out"
          className="grid size-11 cursor-pointer place-items-center rounded-lg text-ink-2 hover:bg-surface-2 focus-visible:outline-2 focus-visible:outline-accent"
        >
          <SignOutIcon aria-hidden size={22} />
        </button>
      </header>

      <main id="main" className="min-w-0 flex-1 px-4 pt-8 pb-28 sm:px-8 md:pt-12 md:pb-16 lg:px-12">
        <div className="mx-auto max-w-5xl">{children}</div>
      </main>

      {/* Phone bottom navigation */}
      <nav
        aria-label="Main"
        className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-3 border-t border-rule bg-surface pb-[env(safe-area-inset-bottom)] md:hidden"
      >
        {NAV.map(({ href, label, Icon }) => (
          <Link
            key={href}
            href={href}
            aria-current={isActive(href) ? "page" : undefined}
            className="flex min-h-16 flex-col items-center justify-center gap-1 text-xs font-semibold text-ink-3 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent aria-[current=page]:text-accent"
          >
            <Icon aria-hidden size={24} weight={isActive(href) ? "fill" : "regular"} />
            {label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
