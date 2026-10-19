"use client";

import { ArrowRightIcon } from "@phosphor-icons/react/ssr";
import { LinkButton } from "@/components/ui";
import { useAuth } from "@/lib/auth";

/** Calls to action on the public home page; they swap to "Go to dashboard" once logged in. */
export function HomeCta({ placement }: { placement: "nav" | "hero" }) {
  const { status } = useAuth();
  const size = placement === "nav" ? "sm" : "md";

  if (status === "authenticated") {
    return (
      <LinkButton href="/dashboard" size={size}>
        Go to dashboard <ArrowRightIcon aria-hidden size={16} weight="bold" />
      </LinkButton>
    );
  }
  return (
    <>
      <LinkButton href="/login" variant={placement === "nav" ? "ghost" : "secondary"} size={size}>
        Log in
      </LinkButton>
      <LinkButton href="/register" size={size}>
        {placement === "hero" ? "Start practising free" : "Create account"}
        {placement === "hero" && <ArrowRightIcon aria-hidden size={16} weight="bold" />}
      </LinkButton>
    </>
  );
}
