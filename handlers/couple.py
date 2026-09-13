"""
🔗 Juftlikka ulanish, username orqali so'rov yuborish, qabul/rad etish, ajratish.
"""
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.queries import (
    create_couple,
    create_pair_request,
    deactivate_couple,
    get_couple_for_user,
    get_pair_request,
    get_partner_user,
    get_or_create_user,
    get_user_by_id,
    update_request_status,
)
from handlers.states import ConnectStates
from keyboards.reply import MAIN_MENU_KB

router = Router(name="couple")


def _connect_menu_kb(has_couple: bool) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🔗 Juftimga ulanish", callback_data="connect:start")],
        [InlineKeyboardButton(text="👤 Username orqali ulanish", callback_data="connect:start")],
    ]
    if has_couple:
        buttons.append([InlineKeyboardButton(text="💔 Juftlikni ajratish", callback_data="connect:unpair")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "connect:menu")
async def connect_menu(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    couple = await get_couple_for_user(session, db_user.id)
    await callback.message.edit_text(
        "🔗 Juftlikka ulanish bo'limi:", reply_markup=_connect_menu_kb(couple is not None)
    )
    await callback.answer()


@router.callback_query(F.data == "connect:start")
async def connect_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    couple = await get_couple_for_user(session, db_user.id)
    if couple is not None:
        await callback.answer("❤️ Siz allaqachon juftlikka ulangansiz.", show_alert=True)
        return
    await state.set_state(ConnectStates.waiting_username)
    await callback.message.answer("👤 Juftingizning Telegram username'ini yuboring (masalan: @username):")
    await callback.answer()


@router.message(ConnectStates.waiting_username, F.text)
async def connect_username_received(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    username = message.text.strip().lstrip("@")
    if not username:
        await message.answer("❌ Username noto'g'ri. Qaytadan yuboring (masalan: @username).")
        return

    couple = await get_couple_for_user(session, db_user.id)
    if couple is not None:
        await state.clear()
        await message.answer("❤️ Siz allaqachon juftlikka ulangansiz.")
        return

    try:
        chat = await message.bot.get_chat(f"@{username}")
    except (TelegramBadRequest, Exception):
        await message.answer("❌ Bunday foydalanuvchi topilmadi. Username'ni tekshirib qaytadan yuboring.")
        return

    if chat.id == message.from_user.id:
        await message.answer("❌ O'zingizni o'zingiz taklif qila olmaysiz.")
        return

    target_user = await get_or_create_user(
        session, telegram_id=chat.id, username=chat.username, first_name=chat.first_name or ""
    )

    target_couple = await get_couple_for_user(session, target_user.id)
    if target_couple is not None:
        await message.answer("❌ Bu foydalanuvchi allaqachon boshqa juftlikka ulangan.")
        await state.clear()
        return

    request = await create_pair_request(session, db_user.id, target_user.id)
    await state.clear()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❤️ Qabul qilish", callback_data=f"connect:accept:{request.id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"connect:reject:{request.id}"),
            ]
        ]
    )
    sender_name = message.from_user.full_name
    sender_username = f"@{message.from_user.username}" if message.from_user.username else ""

    try:
        await message.bot.send_message(
            target_user.telegram_id,
            f"💌 Sizga juftlik ulanish so'rovi keldi.\n👤 {sender_name} {sender_username}",
            reply_markup=kb,
        )
        await message.answer("✅ So'rov yuborildi. Javobini kuting.")
    except TelegramForbiddenError:
        await message.answer(
            "❌ Bu foydalanuvchi botni hali ishga tushirmagan. Undan avval botga /start bosishini so'rang."
        )
        await update_request_status(session, request.id, "failed")


@router.callback_query(F.data.startswith("connect:accept:"))
async def connect_accept(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    request_id = int(callback.data.split(":")[2])
    request = await get_pair_request(session, request_id)
    if request is None or request.status != "pending":
        await callback.answer("❌ Bu so'rov muddati o'tgan.", show_alert=True)
        return

    if request.to_user_id != db_user.id:
        await callback.answer("❌ Bu sizga tegishli emas.", show_alert=True)
        return

    requester_couple = await get_couple_for_user(session, request.from_user_id)
    my_couple = await get_couple_for_user(session, db_user.id)
    if requester_couple is not None or my_couple is not None:
        await update_request_status(session, request.id, "failed")
        await callback.message.edit_text("❌ Bu so'rov endi yaroqsiz.")
        await callback.answer()
        return

    await create_couple(session, request.from_user_id, request.to_user_id)
    await update_request_status(session, request.id, "accepted")

    await callback.message.edit_text("🎉 Juftlik muvaffaqiyatli ulandi!")
    await callback.message.answer("🏠 Asosiy menyu:", reply_markup=MAIN_MENU_KB)

    requester = await get_user_by_id(session, request.from_user_id)
    if requester:
        try:
            await callback.bot.send_message(
                requester.telegram_id, "🎉 Juftlik muvaffaqiyatli ulandi!", reply_markup=MAIN_MENU_KB
            )
        except Exception:
            pass
    await callback.answer()


@router.callback_query(F.data.startswith("connect:reject:"))
async def connect_reject(callback: CallbackQuery, session: AsyncSession) -> None:
    request_id = int(callback.data.split(":")[2])
    request = await get_pair_request(session, request_id)
    if request is None or request.status != "pending":
        await callback.answer("❌ Bu so'rov muddati o'tgan.", show_alert=True)
        return

    await update_request_status(session, request.id, "rejected")
    await callback.message.edit_text("❌ So'rov rad etildi.")

    requester = await get_user_by_id(session, request.from_user_id)
    if requester:
        try:
            await callback.bot.send_message(requester.telegram_id, "❌ Sizning ulanish so'rovingiz rad etildi.")
        except Exception:
            pass
    await callback.answer()


@router.callback_query(F.data == "connect:unpair")
async def connect_unpair_confirm(callback: CallbackQuery) -> None:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💔 Ha, ajratish", callback_data="connect:unpair_yes"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="connect:unpair_no"),
            ]
        ]
    )
    await callback.message.edit_text("⚠️ Haqiqatan ham juftlikni ajratmoqchimisiz?", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "connect:unpair_no")
async def connect_unpair_no(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    couple = await get_couple_for_user(session, db_user.id)
    await callback.message.edit_text("🔗 Juftlikka ulanish bo'limi:", reply_markup=_connect_menu_kb(couple is not None))
    await callback.answer()


@router.callback_query(F.data == "connect:unpair_yes")
async def connect_unpair_yes(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    couple = await get_couple_for_user(session, db_user.id)
    if couple is None:
        await callback.answer("❌ Juftlik topilmadi.", show_alert=True)
        return
    partner = await get_partner_user(session, couple, db_user.id)
    await deactivate_couple(session, couple.id)

    await callback.message.edit_text("💔 Juftlik ajratildi.")
    if partner:
        try:
            await callback.bot.send_message(partner.telegram_id, "💔 Juftingiz aloqani uzdi.")
        except Exception:
            pass
    await callback.answer()
