"""
/start buyrug'i va asosiy menyu.
"""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.reply import MAIN_MENU_KB

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "💕 Xush kelibsiz, JuftimBotbot'ga!\n\n"
        "Bu bot orqali:\n"
        "💕 Sevishganlar uchun — kino, musiqa, rasm va videolar\n"
        "💬 Bizning chat — juftingiz bilan maxsus muloqot\n\n"
        "Boshlash uchun quyidagi menyudan tanlang:",
        reply_markup=MAIN_MENU_KB,
    )
