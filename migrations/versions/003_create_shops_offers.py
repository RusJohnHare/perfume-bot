"""create_shops_offers

Revision ID: 003
Revises: 002
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shops",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("base_url", sa.String(256), nullable=False),
    )
    op.create_table(
        "shop_offers",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("perfume_id", sa.Integer, sa.ForeignKey("perfumes.id"), nullable=False),
        sa.Column("shop_id", sa.Integer, sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("price_rub", sa.Numeric(10, 2), nullable=True),
        sa.Column("in_stock", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_shop_offers_perfume_shop_checked",
                    "shop_offers", ["perfume_id", "shop_id", "checked_at"])
    op.create_index("ix_shop_offers_shop_checked",
                    "shop_offers", ["shop_id", "checked_at"])


def downgrade() -> None:
    op.drop_index("ix_shop_offers_shop_checked", "shop_offers")
    op.drop_index("ix_shop_offers_perfume_shop_checked", "shop_offers")
    op.drop_table("shop_offers")
    op.drop_table("shops")
