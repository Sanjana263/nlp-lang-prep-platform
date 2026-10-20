import type { TargetExam } from "@/lib/api";

const EXAMS: { value: TargetExam; name: string; scale: string }[] = [
  { value: "IELTS", name: "IELTS", scale: "Band 0–9" },
  { value: "TOEFL", name: "TOEFL iBT", scale: "Score 0–120" },
  { value: "PTE", name: "PTE Academic", scale: "Score 10–90" },
];

/** Target exam as a radio group: all three choices visible, each with its own scoring scale. */
export function ExamPicker({ value, onChange }: { value: TargetExam; onChange: (v: TargetExam) => void }) {
  return (
    <fieldset className="grid gap-1.5">
      <legend className="mb-1.5 text-sm font-semibold text-ink">Target exam</legend>
      <div className="grid grid-cols-3 gap-2">
        {EXAMS.map((exam) => (
          <label
            key={exam.value}
            className="relative flex min-h-16 cursor-pointer flex-col justify-center rounded-lg border border-rule-strong bg-surface px-3 py-2.5 transition-colors duration-150 hover:bg-surface-2 has-checked:border-accent has-checked:bg-accent-soft has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-accent"
          >
            <input
              type="radio"
              name="target_exam"
              value={exam.value}
              checked={value === exam.value}
              onChange={() => onChange(exam.value)}
              className="sr-only"
            />
            <span className="text-sm font-semibold text-ink">{exam.name}</span>
            <span className="font-mono text-[11px] text-ink-3">{exam.scale}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
