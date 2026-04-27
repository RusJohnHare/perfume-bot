from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from perfume_bot.bot.keyboards import perfume_card_kb, results_nav_kb
from perfume_bot.bot.states import NoteSelection
from perfume_bot.llm.provider import LLMProvider, PerfumeInfo
from perfume_bot.models.shop import ShopOffer
from perfume_bot.services.recommendation import RecommendationService

router = Router(name="recommendations")
_llm = LLMProvider()

PAGE_SIZE = 1  # одна карточка за раз


async def show_recommendations(message: Message, state: FSMContext, bot: Bot) -> None:
    from perfume_bot.core.database import AsyncSessionLocal
    data = await state.get_data()
    selected_note_ids: list[int] = data.get("selected_notes", [])
    page: int = data.get("results_page", 0)
    result_ids: list[int] = data.get("results", [])

    async with AsyncSessionLocal() as db:
        if not result_ids:
            service = RecommendationService(db)
            results = await service.get_recommendations(selected_note_ids)
            result_ids = [r.perfume.id for r in results]
            await state.update_data(results=result_ids)

        if not result_ids:
            await message.edit_text("😔 По выбранным нотам ничего не найдено. Попробуй расширить выбор.")
            return

        total_pages = len(result_ids)
        if page >= total_pages:
            page = 0

        perfume_id = result_ids[page]

        # Загружаем парфюм с нотами
        from sqlalchemy.orm import selectinload
        from perfume_bot.models.perfume import Perfume, FragranceNote, PerfumeNote
        p_result = await db.execute(
            select(Perfume)
            .where(Perfume.id == perfume_id)
            .options(selectinload(Perfume.perfume_notes).selectinload(PerfumeNote.note))
        )
        perfume = p_result.scalar_one_or_none()
        if not perfume:
            return

        # Актуальная цена
        offer_result = await db.execute(
            select(ShopOffer)
            .where(ShopOffer.perfume_id == perfume_id)
            .order_by(ShopOffer.checked_at.desc())
            .limit(1)
        )
        offer = offer_result.scalar_one_or_none()

        note_names = [pn.note.name for pn in perfume.perfume_notes]
        card_text = _llm.format_recommendation(PerfumeInfo(
            name=perfume.name,
            brand=perfume.brand,
            description=perfume.description,
            notes=note_names,
            price_rub=str(int(offer.price_rub)) if offer and offer.price_rub else None,
            shop_url=offer.url if offer else None,
        ))
        card_text += f"\n\n<i>Парфюм {page + 1} из {total_pages}</i>"

        in_fav = False  # заполняется в Фазе 4
        kb = perfume_card_kb(perfume_id, in_fav, offer.url if offer else None)
        nav_kb = results_nav_kb(page, total_pages)

        # Объединяем кнопки карточки и навигации
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        for row in kb.inline_keyboard:
            builder.row(*row)
        for row in nav_kb.inline_keyboard:
            builder.row(*row)

        await message.edit_text(card_text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(NoteSelection.viewing_results, F.data.startswith("res_page:"))
async def paginate_results(callback: CallbackQuery, state: FSMContext) -> None:
    page = int(callback.data.split(":")[1])
    await state.update_data(results_page=page)
    await show_recommendations(callback.message, state, callback.bot)
    await callback.answer()


@router.callback_query(NoteSelection.viewing_results, F.data == "restart")
async def restart(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    from perfume_bot.bot.keyboards import main_menu_kb
    await callback.message.edit_text("Хорошо, начнём сначала!")
    await callback.message.answer("Выбери действие:", reply_markup=main_menu_kb())
    await callback.answer()
