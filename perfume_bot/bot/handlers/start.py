from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from perfume_bot.bot.keyboards import main_menu_kb

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "👋 Привет! Я помогу тебе подобрать духи по любимым ароматам.\n\n"
        "Нажми «💐 Подобрать духи», чтобы начать, "
        "или «❤️ Моё избранное», чтобы открыть сохранённые парфюмы.",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📖 <b>Как пользоваться ботом:</b>\n\n"
        "1. Нажми «💐 Подобрать духи»\n"
        "2. Выбери категории ароматов и конкретные ноты\n"
        "3. Получи персональную подборку с ценами и ссылками\n"
        "4. Добавляй понравившиеся в избранное — "
        "бот будет следить за ценами и уведомит о скидках 🎉",
        parse_mode="HTML",
    )
