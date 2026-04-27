from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def categories_kb(categories: list[tuple[int, str]], selected_ids: set[int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat_id, cat_name in categories:
        mark = "✅" if cat_id in selected_ids else "⬜"
        builder.button(text=f"{mark} {cat_name}", callback_data=f"cat:{cat_id}")
    builder.button(text="Далее →", callback_data="cat:done")
    builder.adjust(2)
    return builder.as_markup()


def notes_kb(notes: list[tuple[int, str]], selected_ids: set[int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for note_id, note_name in notes:
        mark = "✅" if note_id in selected_ids else "⬜"
        builder.button(text=f"{mark} {note_name}", callback_data=f"note:{note_id}")
    builder.button(text="Показать подборку 🔍", callback_data="note:done")
    builder.adjust(2)
    return builder.as_markup()


def perfume_card_kb(perfume_id: int, in_favorites: bool, shop_url: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    fav_text = "❤️ Убрать из избранного" if in_favorites else "🤍 В избранное"
    fav_action = "fav_remove" if in_favorites else "fav_add"
    builder.button(text=fav_text, callback_data=f"{fav_action}:{perfume_id}")
    if shop_url:
        builder.button(text="🛒 Купить", url=shop_url)
    builder.adjust(1)
    return builder.as_markup()


def results_nav_kb(page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if page > 0:
        builder.button(text="← Назад", callback_data=f"res_page:{page - 1}")
    if page < total_pages - 1:
        builder.button(text="Вперёд →", callback_data=f"res_page:{page + 1}")
    builder.button(text="🔄 Начать заново", callback_data="restart")
    builder.adjust(2)
    return builder.as_markup()


def favorites_item_kb(favorite_id: str, notify: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    notify_text = "🔕 Откл. уведомления" if notify else "🔔 Вкл. уведомления"
    notify_action = "notify_off" if notify else "notify_on"
    builder.button(text=notify_text, callback_data=f"{notify_action}:{favorite_id}")
    builder.button(text="🗑 Убрать из избранного", callback_data=f"fav_del:{favorite_id}")
    builder.adjust(1)
    return builder.as_markup()


def favorites_nav_kb(page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if page > 0:
        builder.button(text="← Назад", callback_data=f"fav_page:{page - 1}")
    if page < total_pages - 1:
        builder.button(text="Вперёд →", callback_data=f"fav_page:{page + 1}")
    builder.adjust(2)
    return builder.as_markup()


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💐 Подобрать духи")],
            [KeyboardButton(text="❤️ Моё избранное")],
        ],
        resize_keyboard=True,
    )
