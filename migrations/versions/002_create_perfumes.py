"""create_perfumes

Revision ID: 002
Revises: 001
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "perfumes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("brand", sa.String(128), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("fragrantica_url", sa.String(512), nullable=True),
    )
    op.create_index("ix_perfumes_brand_name", "perfumes", ["brand", "name"])
    op.create_table(
        "perfume_notes",
        sa.Column("perfume_id", sa.Integer, sa.ForeignKey("perfumes.id"), primary_key=True),
        sa.Column("note_id", sa.Integer, sa.ForeignKey("fragrance_notes.id"), primary_key=True),
        sa.Column("note_type", sa.String(8), nullable=False, server_default="main"),
        sa.CheckConstraint("note_type IN ('top','middle','base','main')", name="ck_note_type"),
    )


def downgrade() -> None:
    op.drop_table("perfume_notes")
    op.drop_index("ix_perfumes_brand_name", "perfumes")
    op.drop_table("perfumes")
