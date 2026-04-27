import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, ForeignKey, Boolean, DECIMAL, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from perfume_bot.models.base import Base


class Shop(Base):
    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    base_url: Mapped[str] = mapped_column(String(256), nullable=False)

    offers: Mapped[list["ShopOffer"]] = relationship(back_populates="shop")


class ShopOffer(Base):
    """Append-only: записи только добавляются, UPDATE/DELETE запрещены."""

    __tablename__ = "shop_offers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    perfume_id: Mapped[int] = mapped_column(ForeignKey("perfumes.id"), nullable=False)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    price_rub: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2))
    in_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    perfume: Mapped["Perfume"] = relationship(back_populates="offers")  # noqa: F821
    shop: Mapped[Shop] = relationship(back_populates="offers")
