import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from perfume_bot.models import FragranceCategory, FragranceNote, Perfume, PerfumeNote
from perfume_bot.services.recommendation import RecommendationService


@pytest.fixture
async def seeded_db(db_session: AsyncSession):
    cat = FragranceCategory(name="Тестовые")
    db_session.add(cat)
    await db_session.flush()

    notes = [FragranceNote(name=f"Нота{i}", category_id=cat.id) for i in range(1, 8)]
    db_session.add_all(notes)
    await db_session.flush()

    # Создаём 7 парфюмов с разными наборами нот
    for i in range(7):
        p = Perfume(name=f"Парфюм{i}", brand="Бренд")
        db_session.add(p)
        await db_session.flush()
        # Каждый парфюм имеет 2–3 ноты
        for j in range(i % 3 + 1):
            note_idx = (i + j) % len(notes)
            db_session.add(PerfumeNote(perfume_id=p.id, note_id=notes[note_idx].id))

    await db_session.commit()
    return notes


async def test_returns_at_least_5_results(seeded_db, db_session: AsyncSession):
    notes = seeded_db
    service = RecommendationService(db_session)
    selected_note_ids = [notes[0].id, notes[1].id]
    results = await service.get_recommendations(selected_note_ids)
    assert len(results) >= 5


async def test_fallback_with_partial_matches(db_session: AsyncSession):
    """При каталоге меньше 5 позиций — возвращает все доступные."""
    cat = FragranceCategory(name="Мало")
    db_session.add(cat)
    await db_session.flush()
    note = FragranceNote(name="УникальнаяНота", category_id=cat.id)
    db_session.add(note)
    await db_session.flush()

    p = Perfume(name="ОдинParfum", brand="X")
    db_session.add(p)
    await db_session.flush()
    db_session.add(PerfumeNote(perfume_id=p.id, note_id=note.id))
    await db_session.commit()

    service = RecommendationService(db_session)
    results = await service.get_recommendations([note.id])
    assert len(results) >= 1
