"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";

const primary =
  "rounded-lg bg-indigo-600 px-5 py-3 text-sm font-medium text-white hover:bg-indigo-500";
const secondary =
  "rounded-lg border border-zinc-300 px-5 py-3 text-sm font-medium hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800";

export function HomeCta() {
  const { status } = useAuth();
  if (status === "authenticated") {
    return (
      <Link href="/dashboard" className={primary}>
        Go to dashboard
      </Link>
    );
  }
  return (
    <>
      <Link href="/register" className={primary}>
        Create free account
      </Link>
      <Link href="/login" className={secondary}>
        Log in
      </Link>
    </>
  );
}
