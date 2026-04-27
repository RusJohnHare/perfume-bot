"""create_categories_notes

Revision ID: 001
Revises:
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fragrance_categories",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
    )
    op.create_table(
        "fragrance_notes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("fragrance_categories.id"), nullable=False),
    )
    op.create_index("ix_fragrance_notes_category_id", "fragrance_notes", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_fragrance_notes_category_id", "fragrance_notes")
    op.drop_table("fragrance_notes")
    op.drop_table("fragrance_categories")
