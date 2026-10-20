"""speaking assessment columns

Revision ID: b7e41c2a9d10
Revises: 8353298dbc14
Create Date: 2026-10-20 10:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b7e41c2a9d10"
down_revision = "8353298dbc14"
branch_labels = None
depends_on = None

COLUMNS = [
    sa.Column("prompt_id", sa.String(length=40), nullable=True),
    sa.Column("prompt_text", sa.Text(), nullable=True),
    sa.Column("duration_seconds", sa.Float(), nullable=True),
    sa.Column("lexical_score", sa.Float(), nullable=True),
    sa.Column("grammar_score", sa.Float(), nullable=True),
    sa.Column("overall_band", sa.Float(), nullable=True),
    sa.Column("analysis_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column("error_message", sa.Text(), nullable=True),
]


def upgrade() -> None:
    for column in COLUMNS:
        op.add_column("speaking_submissions", column)


def downgrade() -> None:
    for column in reversed(COLUMNS):
        op.drop_column("speaking_submissions", column.name)
