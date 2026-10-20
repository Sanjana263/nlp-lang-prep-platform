"use client";

import { useEffect, useId, useRef } from "react";
import { WarningCircleIcon } from "@phosphor-icons/react/ssr";
import { Badge, Button } from "@/components/ui";

/** In-app modal for errors the learner must notice. Uses the native <dialog>: focus is trapped, Esc closes it. */
export function AlertDialog({
  message,
  label = "Error",
  onClose,
}: {
  message: string | null;
  label?: string;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const id = useId();
  const open = message !== null;

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      role="alertdialog"
      aria-labelledby={`${id}-label`}
      aria-describedby={`${id}-message`}
      onClose={onClose}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose(); // click on the backdrop
      }}
      className="m-auto w-[min(92vw,26rem)] rounded-xl border border-rule bg-surface p-0 text-ink shadow-2xl backdrop:bg-black/55"
    >
      <div className="grid gap-4 p-6">
        <div className="flex items-center gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-full bg-red-soft text-red-pen">
            <WarningCircleIcon aria-hidden size={24} weight="bold" />
          </span>
          <span id={`${id}-label`}>
            <Badge tone="danger">{label}</Badge>
          </span>
        </div>
        <p id={`${id}-message`} className="text-[15px] leading-6 text-ink">
          {message}
        </p>
        <Button onClick={onClose} autoFocus className="justify-self-end">
          OK
        </Button>
      </div>
    </dialog>
  );
}
