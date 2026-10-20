"""writing prompts question bank

Revision ID: c3d52f8e7a41
Revises: b7e41c2a9d10
Create Date: 2026-10-21 12:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "c3d52f8e7a41"
down_revision = "b7e41c2a9d10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "writing_prompts",
        sa.Column("prompt_id", sa.Integer(), nullable=False),
        sa.Column("writing_type", sa.String(length=20), server_default="essay", nullable=False),
        sa.Column("topic", sa.String(length=50), nullable=False),
        sa.Column("question_type", sa.String(length=30), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "writing_type IN ('essay','letter','report','graph_description')",
            name="ck_writing_prompts_type",
        ),
        sa.PrimaryKeyConstraint("prompt_id"),
        sa.UniqueConstraint("prompt_text"),
    )
    op.create_index(op.f("ix_writing_prompts_writing_type"), "writing_prompts", ["writing_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_writing_prompts_writing_type"), table_name="writing_prompts")
    op.drop_table("writing_prompts")