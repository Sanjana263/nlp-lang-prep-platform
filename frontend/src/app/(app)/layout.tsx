"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { Spinner } from "@/components/ui";
import { useAuth } from "@/lib/auth";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/writing", label: "Writing" },
  { href: "/settings", label: "Settings" },
];
const SOON = ["Reading", "Listening", "Speaking", "Vocabulary"];

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
      <div className="flex flex-1 items-center justify-center text-zinc-500">
        <Spinner />
      </div>
    );
  }

  const linkClass = (href: string) =>
    `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
      pathname === href
        ? "bg-indigo-600 text-white"
        : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
    }`;

  return (
    <div className="flex flex-1 flex-col md:flex-row">
      <aside className="border-b border-zinc-200 p-4 md:w-56 md:border-r md:border-b-0 dark:border-zinc-800">
        <div className="flex items-center justify-between md:block">
          <Link href="/dashboard" className="text-lg font-semibold tracking-tight">
            Cadence
          </Link>
          <button onClick={logout} className="text-sm text-zinc-500 hover:underline md:mt-0 md:hidden">
            Log out
          </button>
        </div>
        <nav className="mt-3 flex gap-1 overflow-x-auto md:mt-8 md:flex-col" aria-label="Main">
          {NAV.map((n) => (
            <Link key={n.href} href={n.href} className={linkClass(n.href)}>
              {n.label}
            </Link>
          ))}
          {SOON.map((label) => (
            <span
              key={label}
              className="hidden items-center justify-between rounded-lg px-3 py-2 text-sm text-zinc-400 md:flex"
            >
              {label}
              <span className="text-[10px] uppercase tracking-wide">Soon</span>
            </span>
          ))}
        </nav>
        <div className="mt-8 hidden md:block">
          <p className="truncate text-sm font-medium">{user.full_name}</p>
          <p className="truncate text-xs text-zinc-500">{user.email}</p>
          <button onClick={logout} className="mt-3 text-sm text-zinc-500 hover:underline">
            Log out
          </button>
        </div>
      </aside>
      <main className="flex-1 px-4 py-8 md:px-10">
        <div className="mx-auto max-w-4xl">{children}</div>
      </main>
    </div>
  );
}
