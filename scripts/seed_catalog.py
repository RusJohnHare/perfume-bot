"""
Загрузка каталога парфюмерии из CSV-файла Fragrantica (Kaggle).

Использование:
    python scripts/seed_catalog.py --csv /path/to/fragrantica.csv
    python scripts/seed_catalog.py --csv /path/to/fragrantica.csv --dry-run
"""
import argparse
import asyncio
import csv
import sys
from pathlib import Path

# Ожидаемые колонки CSV (Kaggle Fragrantica dataset)
COL_NAME = "Name"
COL_BRAND = "Brand"
COL_DESCRIPTION = "Description"
COL_NOTES_TOP = "Top Notes"
COL_NOTES_MIDDLE = "Middle Notes"
COL_NOTES_BASE = "Base Notes"

# Категории по умолчанию
DEFAULT_CATEGORIES = [
    "Цитрусовые", "Древесные", "Цветочные", "Мускусные",
    "Восточные", "Свежие", "Пряные", "Фужерные", "Шипровые", "Гурманские",
]


async def seed(csv_path: Path, dry_run: bool = False) -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy import select
    from perfume_bot.core.config import settings
    from perfume_bot.models import (
        FragranceCategory, FragranceNote, Perfume, PerfumeNote,
        Shop,
    )

    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        # 1. Создаём категории
        categories: dict[str, FragranceCategory] = {}
        for cat_name in DEFAULT_CATEGORIES:
            result = await session.execute(
                select(FragranceCategory).where(FragranceCategory.name == cat_name)
            )
            cat = result.scalar_one_or_none()
            if cat is None:
                cat = FragranceCategory(name=cat_name)
                session.add(cat)
            categories[cat_name] = cat
        await session.flush()

        # 2. Вспомогательная функция: получить/создать ноту
        notes_cache: dict[str, FragranceNote] = {}

        async def get_or_create_note(name: str) -> FragranceNote:
            name = name.strip()
            if name in notes_cache:
                return notes_cache[name]
            result = await session.execute(
                select(FragranceNote).where(FragranceNote.name == name)
            )
            note = result.scalar_one_or_none()
            if note is None:
                # Без категоризации — кладём в "Свежие" как дефолт
                note = FragranceNote(name=name, category_id=categories["Свежие"].id)
                session.add(note)
                await session.flush()
            notes_cache[name] = note
            return note

        # 3. Создаём магазины (если ещё нет)
        shops_data = [
            ("Randewoo", "https://randewoo.ru"),
            ("Notino", "https://www.notino.ru"),
            ("Золотое Яблоко", "https://goldapple.ru"),
            ("Летуаль", "https://www.letu.ru"),
        ]
        for shop_name, shop_url in shops_data:
            result = await session.execute(select(Shop).where(Shop.name == shop_name))
            if result.scalar_one_or_none() is None:
                session.add(Shop(name=shop_name, base_url=shop_url))
        await session.flush()

        # 4. Читаем CSV и создаём парфюмы
        count = 0
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = (row.get(COL_NAME) or "").strip()
                brand = (row.get(COL_BRAND) or "").strip()
                if not name or not brand:
                    continue

                perfume = Perfume(
                    name=name,
                    brand=brand,
                    description=(row.get(COL_DESCRIPTION) or "").strip() or None,
                )
                session.add(perfume)
                await session.flush()

                for note_str, note_type in [
                    (row.get(COL_NOTES_TOP, ""), "top"),
                    (row.get(COL_NOTES_MIDDLE, ""), "middle"),
                    (row.get(COL_NOTES_BASE, ""), "base"),
                ]:
                    for raw_note in (note_str or "").split(","):
                        raw_note = raw_note.strip()
                        if raw_note:
                            note_obj = await get_or_create_note(raw_note)
                            session.add(PerfumeNote(
                                perfume_id=perfume.id,
                                note_id=note_obj.id,
                                note_type=note_type,
                            ))

                count += 1
                if count % 500 == 0:
                    print(f"  Обработано: {count} парфюмов...")

        if dry_run:
            await session.rollback()
            print(f"Dry run: обработано {count} парфюмов, изменения не сохранены.")
        else:
            await session.commit()
            print(f"Загружено {count} парфюмов.")

    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Загрузка каталога Fragrantica из CSV")
    parser.add_argument("--csv", required=True, help="Путь к CSV-файлу")
    parser.add_argument("--dry-run", action="store_true", help="Проверка без сохранения")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Файл не найден: {csv_path}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(seed(csv_path, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
