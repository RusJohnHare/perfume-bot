import uuid
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from perfume_bot.bot.keyboards import favorites_item_kb, favorites_nav_kb, main_menu_kb
from perfume_bot.bot.states import FavoritesMenu, NoteSelection
from perfume_bot.models.favorite import Favorite
from perfume_bot.models.perfume import Perfume
from perfume_bot.models.shop import ShopOffer
from perfume_bot.services.favorites import FavoritesService

router = Router(name="favorites")
PAGE_SIZE = 3


async def _get_or_create_user(tg_user_id: int, db: AsyncSession):
    from perfume_bot.models.user import User
    result = await db.execute(select(User).where(User.tg_user_id == tg_user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(tg_user_id=tg_user_id)
        db.add(user)
        await db.commit()
    return user


@router.message(F.text == "❤️ Моё избранное")
@router.message(Command("favorites"))
async def show_favorites(message: Message, state: FSMContext, db: AsyncSession) -> None:
    user = await _get_or_create_user(message.from_user.id, db)
    service = FavoritesService(db)
    favorites = await service.list_for_user(user.id)

    if not favorites:
        await message.answer(
            "❤️ <b>Избранное пусто</b>\n\n"
            "Добавляй духи из подборки и я буду следить за ценами!",
            reply_markup=main_menu_kb(),
            parse_mode="HTML",
        )
        return

    await state.set_state(FavoritesMenu.viewing_list)
    await state.update_data(favorites_page=0)
    await _send_favorites_page(message, favorites, 0, send_new=True)


async def _send_favorites_page(
    message: Message, favorites: list[Favorite], page: int, send_new: bool = False
) -> None:
    start = page * PAGE_SIZE
    page_items = favorites[start: start + PAGE_SIZE]
    total_pages = max(1, -(-len(favorites) // PAGE_SIZE))

    text_parts = [f"❤️ <b>Избранное</b> ({len(favorites)} парфюмов)\n"]
    for fav in page_items:
        perfume = fav.perfume
        notify_icon = "🔔" if fav.notify_on_price_drop else "🔕"
        text_parts.append(f"{notify_icon} <b>{perfume.name}</b> — {perfume.brand}")

    text = "\n".join(text_parts)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for fav in page_items:
        for row in favorites_item_kb(str(fav.id), fav.notify_on_price_drop).inline_keyboard:
            builder.row(*row)
    for row in favorites_nav_kb(page, total_pages).inline_keyboard:
        builder.row(*row)

    if send_new:
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(FavoritesMenu.viewing_list, F.data.startswith("fav_del:"))
async def remove_favorite(callback: CallbackQuery, state: FSMContext, db: AsyncSession) -> None:
    fav_id = uuid.UUID(callback.data.split(":")[1])
    user = await _get_or_create_user(callback.from_user.id, db)
    service = FavoritesService(db)
    await service.remove(fav_id)
    favorites = await service.list_for_user(user.id)
    if not favorites:
        await state.clear()
        await callback.message.edit_text(
            "❤️ Избранное теперь пусто. Нажми «💐 Подобрать духи», чтобы найти новые парфюмы!"
        )
    else:
        data = await state.get_data()
        page = data.get("favorites_page", 0)
        await _send_favorites_page(callback.message, favorites, page)
    await callback.answer("Удалено из избранного")


@router.callback_query(F.data.startswith("notify_on:") | F.data.startswith("notify_off:"))
async def toggle_notify(callback: CallbackQuery, db: AsyncSession) -> None:
    fav_id = uuid.UUID(callback.data.split(":")[1])
    service = FavoritesService(db)
    fav = await service.toggle_notify(fav_id)
    status = "включены 🔔" if fav.notify_on_price_drop else "отключены 🔕"
    await callback.answer(f"Уведомления {status}")
    await callback.message.edit_reply_markup(
        reply_markup=favorites_item_kb(str(fav_id), fav.notify_on_price_drop)
    )


@router.callback_query(F.data.startswith("fav_add:"))
async def add_to_favorites(callback: CallbackQuery, db: AsyncSession) -> None:
    perfume_id = int(callback.data.split(":")[1])
    user = await _get_or_create_user(callback.from_user.id, db)
    service = FavoritesService(db)
    await service.add(user.id, perfume_id)
    await callback.answer("Добавлено в избранное ❤️")


@router.callback_query(F.data.startswith("fav_remove:"))
async def remove_from_card(callback: CallbackQuery, db: AsyncSession) -> None:
    perfume_id = int(callback.data.split(":")[1])
    user = await _get_or_create_user(callback.from_user.id, db)
    service = FavoritesService(db)
    favorites = await service.list_for_user(user.id)
    for fav in favorites:
        if fav.perfume_id == perfume_id:
            await service.remove(fav.id)
            break
    await callback.answer("Убрано из избранного 🤍")


@router.callback_query(FavoritesMenu.viewing_list, F.data.startswith("fav_page:"))
async def paginate_favorites(callback: CallbackQuery, state: FSMContext, db: AsyncSession) -> None:
    page = int(callback.data.split(":")[1])
    await state.update_data(favorites_page=page)
    user = await _get_or_create_user(callback.from_user.id, db)
    service = FavoritesService(db)
    favorites = await service.list_for_user(user.id)
    await _send_favorites_page(callback.message, favorites, page)
    await callback.answer()
