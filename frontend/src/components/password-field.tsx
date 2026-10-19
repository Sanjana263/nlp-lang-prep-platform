"use client";

import { useState, type InputHTMLAttributes } from "react";
import { EyeIcon, EyeSlashIcon } from "@phosphor-icons/react/ssr";
import { describedBy, inputClass } from "@/components/ui";

export function PasswordField({
  id,
  label,
  hint,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { id: string; label: string; hint?: string }) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="grid gap-1.5">
      <label htmlFor={id} className="text-sm font-semibold text-ink">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={visible ? "text" : "password"}
          className={`${inputClass} pr-12`}
          aria-describedby={describedBy(id, hint)}
          {...props}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Hide password" : "Show password"}
          aria-pressed={visible}
          className="absolute inset-y-0 right-0 flex w-11 cursor-pointer items-center justify-center rounded-r-lg text-ink-3 hover:text-ink focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
        >
          {visible ? <EyeSlashIcon aria-hidden size={20} /> : <EyeIcon aria-hidden size={20} />}
        </button>
      </div>
      {hint && (
        <p id={`${id}-hint`} className="text-sm text-ink-3">
          {hint}
        </p>
      )}
    </div>
  );
}
