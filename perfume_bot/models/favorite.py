import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from perfume_bot.models.base import Base


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "perfume_id", name="uq_user_perfume"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    perfume_id: Mapped[int] = mapped_column(ForeignKey("perfumes.id"), nullable=False)
    notify_on_price_drop: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="favorites")  # noqa: F821
    perfume: Mapped["Perfume"] = relationship(back_populates="favorites")  # noqa: F821
