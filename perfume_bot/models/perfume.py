from sqlalchemy import String, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from perfume_bot.models.base import Base


class FragranceCategory(Base):
    __tablename__ = "fragrance_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    notes: Mapped[list["FragranceNote"]] = relationship(back_populates="category")


class FragranceNote(Base):
    __tablename__ = "fragrance_notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("fragrance_categories.id"), nullable=False)

    category: Mapped[FragranceCategory] = relationship(back_populates="notes")
    perfume_notes: Mapped[list["PerfumeNote"]] = relationship(back_populates="note")


class Perfume(Base):
    __tablename__ = "perfumes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    brand: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    fragrantica_url: Mapped[str | None] = mapped_column(String(512))

    perfume_notes: Mapped[list["PerfumeNote"]] = relationship(back_populates="perfume")
    offers: Mapped[list["ShopOffer"]] = relationship(back_populates="perfume")  # noqa: F821
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="perfume")  # noqa: F821


class PerfumeNote(Base):
    __tablename__ = "perfume_notes"
    __table_args__ = (
        CheckConstraint("note_type IN ('top','middle','base','main')", name="ck_note_type"),
    )

    perfume_id: Mapped[int] = mapped_column(ForeignKey("perfumes.id"), primary_key=True)
    note_id: Mapped[int] = mapped_column(ForeignKey("fragrance_notes.id"), primary_key=True)
    note_type: Mapped[str] = mapped_column(String(8), nullable=False, default="main")

    perfume: Mapped[Perfume] = relationship(back_populates="perfume_notes")
    note: Mapped[FragranceNote] = relationship(back_populates="perfume_notes")
