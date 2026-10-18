import Link from "next/link";
import type { ReactNode } from "react";

export function AuthCard({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <main className="flex flex-1 items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <Link href="/" className="mb-8 block text-center text-2xl font-semibold tracking-tight">
          Cadence
        </Link>
        <div className="rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <h1 className="text-xl font-semibold">{title}</h1>
          <p className="mt-1 mb-6 text-sm text-zinc-500 dark:text-zinc-400">{subtitle}</p>
          {children}
        </div>
      </div>
    </main>
  );
}
