"""Load the writing question bank into the writing_prompts table.

Run from backend/ (after `npm run migrate`):   python -m scripts.seed_writing_prompts
Safe to re-run: questions already in the table are skipped, nothing is deleted or changed.
"""
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import WritingPrompt
from app.writing.prompt_bank import PROMPT_BANK


def main() -> None:
    with SessionLocal() as db:
        existing = set(db.scalars(select(WritingPrompt.prompt_text)))
        added = 0
        for topic, question_type, text in PROMPT_BANK:
            if text in existing:
                continue
            db.add(WritingPrompt(writing_type="essay", topic=topic, question_type=question_type, prompt_text=text))
            existing.add(text)
            added += 1
        db.commit()
        total = len(existing)
    print(f"Added {added} new writing question(s). The table now holds {total}.")


if __name__ == "__main__":
    main()
