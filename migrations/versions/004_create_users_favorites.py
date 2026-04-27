"""create_users_favorites

Revision ID: 004
Revises: 003
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("tg_user_id", sa.BigInteger, nullable=False, unique=True),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_users_tg_user_id", "users", ["tg_user_id"], unique=True)
    op.create_table(
        "favorites",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("user_id", sa.Uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("perfume_id", sa.Integer, sa.ForeignKey("perfumes.id"), nullable=False),
        sa.Column("notify_on_price_drop", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.UniqueConstraint("user_id", "perfume_id", name="uq_user_perfume"),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])
    op.create_index("ix_favorites_notify", "favorites", ["notify_on_price_drop"])


def downgrade() -> None:
    op.drop_index("ix_favorites_notify", "favorites")
    op.drop_index("ix_favorites_user_id", "favorites")
    op.drop_table("favorites")
    op.drop_index("ix_users_tg_user_id", "users")
    op.drop_table("users")
