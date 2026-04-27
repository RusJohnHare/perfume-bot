from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from perfume_bot.bot.keyboards import categories_kb, notes_kb
from perfume_bot.bot.states import NoteSelection
from perfume_bot.models.perfume import FragranceCategory, FragranceNote

router = Router(name="notes")


@router.message(F.text == "💐 Подобрать духи")
async def start_selection(message: Message, state: FSMContext, db: AsyncSession) -> None:
    await state.clear()
    result = await db.execute(select(FragranceCategory).order_by(FragranceCategory.name))
    categories = result.scalars().all()
    if not categories:
        await message.answer("😔 Каталог пока пуст. Попробуйте позже.")
        return

    cats = [(c.id, c.name) for c in categories]
    await state.set_state(NoteSelection.choosing_categories)
    await state.update_data(selected_categories=[], selected_notes=[], categories=cats)
    await message.answer(
        "🌸 <b>Шаг 1 из 2:</b> Выбери категории ароматов, которые тебе нравятся.\n"
        "(можно несколько)",
        reply_markup=categories_kb(cats, set()),
        parse_mode="HTML",
    )


@router.callback_query(NoteSelection.choosing_categories, F.data.startswith("cat:"))
async def toggle_category(callback: CallbackQuery, state: FSMContext, db: AsyncSession) -> None:
    data = await state.get_data()
    cats: list[tuple[int, str]] = data.get("categories", [])
    selected: list[int] = data.get("selected_categories", [])
    value = callback.data.split(":")[1]

    if value == "done":
        if not selected:
            await callback.answer("Выбери хотя бы одну категорию!", show_alert=True)
            return
        # Загружаем ноты выбранных категорий
        result = await db.execute(
            select(FragranceNote)
            .where(FragranceNote.category_id.in_(selected))
            .order_by(FragranceNote.name)
        )
        notes_list = [(n.id, n.name) for n in result.scalars().all()]
        await state.set_state(NoteSelection.choosing_notes)
        await state.update_data(notes=notes_list, selected_notes=[])
        await callback.message.edit_text(
            "🎵 <b>Шаг 2 из 2:</b> Выбери конкретные ноты, которые тебе нравятся.",
            reply_markup=notes_kb(notes_list, set()),
            parse_mode="HTML",
        )
    else:
        cat_id = int(value)
        if cat_id in selected:
            selected.remove(cat_id)
        else:
            selected.append(cat_id)
        await state.update_data(selected_categories=selected)
        await callback.message.edit_reply_markup(
            reply_markup=categories_kb(cats, set(selected))
        )

    await callback.answer()


@router.callback_query(NoteSelection.choosing_notes, F.data.startswith("note:"))
async def toggle_note(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    notes: list[tuple[int, str]] = data.get("notes", [])
    selected: list[int] = data.get("selected_notes", [])
    value = callback.data.split(":")[1]

    if value == "done":
        if not selected:
            await callback.answer("Выбери хотя бы одну ноту!", show_alert=True)
            return
        # Передаём управление обработчику рекомендаций
        await state.set_state(NoteSelection.viewing_results)
        await state.update_data(results_page=0)
        # Триггерим показ рекомендаций через отдельный роутер
        await callback.message.edit_text("🔍 Подбираю парфюмы...")
        from perfume_bot.bot.handlers.recommendations import show_recommendations
        await show_recommendations(callback.message, state, callback.bot)
    else:
        note_id = int(value)
        if note_id in selected:
            selected.remove(note_id)
        else:
            selected.append(note_id)
        await state.update_data(selected_notes=selected)
        await callback.message.edit_reply_markup(
            reply_markup=notes_kb(notes, set(selected))
        )

    await callback.answer()
