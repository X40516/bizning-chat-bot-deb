"""
💬 Bizning chat - juftlik o'rtasidagi to'g'ridan-to'g'ri xabar almashish.
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.queries import get_couple_for_user, get_partner_user, log_message
from handlers.couple import _connect_menu_kb
from handlers.states import ChatStates
from keyboards.reply import BACK_ONLY_KB, MAIN_MENU_KB
from utils.helpers import build_partner_status_text, detect_message_type

router = Router(name="chat")


@router.message(F.text == "💬 Bizning chat")
async def chat_entry(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    couple = await get_couple_for_user(session, db_user.id)
    if couple is None:
        await message.answer(
            "💬 Hali juftingiz yo'q. Ulanish uchun quyidagi bo'limlardan birini tanlang:",
            reply_markup=_connect_menu_kb(False),
        )
        return

    partner = await get_partner_user(session, couple, db_user.id)
    status_text = build_partner_status_text(partner) if partner else ""
    await state.set_state(ChatStates.active)
    await message.answer(
        f"💬 Bizning chat\n{status_text}\n\n"
        "Yozgan xabaringiz avtomatik ravishda juftingizga yetkaziladi.\n"
        "Chiqish uchun '⬅️ Orqaga' tugmasini bosing.",
        reply_markup=BACK_ONLY_KB,
    )


@router.message(ChatStates.active, F.text == "⬅️ Orqaga")
async def chat_exit(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("🏠 Asosiy menyu:", reply_markup=MAIN_MENU_KB)


@router.message(ChatStates.active)
async def chat_relay(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    couple = await get_couple_for_user(session, db_user.id)
    if couple is None:
        await state.clear()
        await message.answer("❌ Juftlik topilmadi.", reply_markup=MAIN_MENU_KB)
        return

    partner = await get_partner_user(session, couple, db_user.id)
    if partner is None:
        await state.clear()
        await message.answer("❌ Juftingiz topilmadi.", reply_markup=MAIN_MENU_KB)
        return

    try:
        await message.bot.copy_message(
            chat_id=partner.telegram_id, from_chat_id=message.chat.id, message_id=message.message_id
        )
        msg_type = detect_message_type(message)
        await log_message(session, couple.id, db_user.id, msg_type, message.message_id)
    except Exception:
        await message.answer("❌ Xabar yetkazilmadi. Juftingiz botni bloklagan bo'lishi mumkin.")
