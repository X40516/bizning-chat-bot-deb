"""
👨‍💼 Admin panel - kontentni boshqarish (kino, musiqa, rasm, video).
"""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDS
from database.queries import add_content, delete_content, get_content_by_id, get_content_list, update_content_field
from handlers.content import TYPE_LABELS
from handlers.states import AdminContentStates

router = Router(name="admin")
router.message.filter(F.from_user.id.in_(ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(ADMIN_IDS))


def _admin_type_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"admin:type:{ctype}")]
            for ctype, label in TYPE_LABELS.items()
        ]
    )


def _admin_actions_kb(content_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Qo'shish", callback_data=f"admin:add:{content_type}")],
            [InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"admin:delmenu:{content_type}")],
            [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"admin:editmenu:{content_type}")],
            [InlineKeyboardButton(text="📋 Ro'yxat", callback_data=f"admin:listview:{content_type}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu")],
        ]
    )


@router.message(Command("admin"))
async def admin_menu(message: Message) -> None:
    await message.answer("👨‍💼 Admin panel — kontent turini tanlang:", reply_markup=_admin_type_menu_kb())


@router.callback_query(F.data == "admin:menu")
async def admin_menu_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text("👨‍💼 Admin panel — kontent turini tanlang:", reply_markup=_admin_type_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:type:"))
async def admin_type_menu(callback: CallbackQuery) -> None:
    content_type = callback.data.split(":")[2]
    label = TYPE_LABELS.get(content_type, content_type)
    await callback.message.edit_text(f"{label} boshqaruvi:", reply_markup=_admin_actions_kb(content_type))
    await callback.answer()


# ---------- Qo'shish ----------

FILE_TYPE_PROMPTS = {
    "movie": "🎬 Kino faylini (video yoki hujjat) yuboring:",
    "music": "🎵 Musiqa faylini (audio) yuboring:",
    "photo": "🖼️ Rasm faylini yuboring:",
    "video": "🎥 Video faylini yuboring:",
}


@router.callback_query(F.data.startswith("admin:add:"))
async def admin_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    content_type = callback.data.split(":")[2]
    await state.set_state(AdminContentStates.waiting_file)
    await state.update_data(content_type=content_type)
    await callback.message.answer(FILE_TYPE_PROMPTS.get(content_type, "Faylni yuboring:"))
    await callback.answer()


def _extract_file_id(message: Message) -> str | None:
    if message.video:
        return message.video.file_id
    if message.audio:
        return message.audio.file_id
    if message.photo:
        return message.photo[-1].file_id
    if message.document:
        return message.document.file_id
    return None


@router.message(AdminContentStates.waiting_file)
async def admin_add_file_received(message: Message, state: FSMContext) -> None:
    file_id = _extract_file_id(message)
    if file_id is None:
        await message.answer("❌ Fayl aniqlanmadi. Video, audio, rasm yoki hujjat yuboring.")
        return

    await state.update_data(telegram_file_id=file_id)
    await state.set_state(AdminContentStates.waiting_title)
    await message.answer("📝 Nomini yozing:")


@router.message(AdminContentStates.waiting_title, F.text)
async def admin_add_title_received(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminContentStates.waiting_description)
    await message.answer("📝 Tavsifini yozing (yoki '-' o'tkazib yuborish uchun):")


@router.message(AdminContentStates.waiting_description, F.text)
async def admin_add_description_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    description = "" if message.text.strip() == "-" else message.text.strip()
    await state.update_data(description=description)

    data = await state.get_data()
    content_type = data["content_type"]

    if content_type == "music":
        await state.set_state(AdminContentStates.waiting_artist)
        await message.answer("🎤 Ijrochi nomini yozing (yoki '-' o'tkazib yuborish uchun):")
        return
    if content_type == "movie":
        await state.set_state(AdminContentStates.waiting_genre)
        await message.answer("🏷️ Janrini yozing (yoki '-' o'tkazib yuborish uchun):")
        return

    await _save_content(message, state, session)


@router.message(AdminContentStates.waiting_artist, F.text)
async def admin_add_artist_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    artist = None if message.text.strip() == "-" else message.text.strip()
    await state.update_data(artist=artist)
    await _save_content(message, state, session)


@router.message(AdminContentStates.waiting_genre, F.text)
async def admin_add_genre_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    genre = None if message.text.strip() == "-" else message.text.strip()
    await state.update_data(genre=genre)
    await _save_content(message, state, session)


async def _save_content(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await add_content(
        session,
        content_type=data["content_type"],
        title=data["title"],
        description=data.get("description", ""),
        telegram_file_id=data["telegram_file_id"],
        artist=data.get("artist"),
        genre=data.get("genre"),
    )
    await state.clear()
    await message.answer("✅ Kontent muvaffaqiyatli qo'shildi!")


# ---------- O'chirish ----------

@router.callback_query(F.data.startswith("admin:delmenu:"))
async def admin_delete_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    content_type = callback.data.split(":")[2]
    items = await get_content_list(session, content_type)
    if not items:
        await callback.answer("📭 Kontent yo'q.", show_alert=True)
        return

    buttons = [[InlineKeyboardButton(text=f"🗑️ {i.title}", callback_data=f"admin:del:{i.id}:{content_type}")] for i in items]
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admin:type:{content_type}")])
    await callback.message.edit_text("O'chirmoqchi bo'lgan kontentni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:del:"))
async def admin_delete_confirm(callback: CallbackQuery) -> None:
    _, _, content_id, content_type = callback.data.split(":")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑️ Ha, o'chirish", callback_data=f"admin:delyes:{content_id}:{content_type}"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data=f"admin:type:{content_type}"),
            ]
        ]
    )
    await callback.message.edit_text("⚠️ Haqiqatan ham o'chirmoqchimisiz?", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:delyes:"))
async def admin_delete_yes(callback: CallbackQuery, session: AsyncSession) -> None:
    _, _, content_id, content_type = callback.data.split(":")
    await delete_content(session, int(content_id))
    await callback.message.edit_text("✅ O'chirildi.", reply_markup=_admin_actions_kb(content_type))
    await callback.answer()


# ---------- Tahrirlash ----------

@router.callback_query(F.data.startswith("admin:editmenu:"))
async def admin_edit_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    content_type = callback.data.split(":")[2]
    items = await get_content_list(session, content_type)
    if not items:
        await callback.answer("📭 Kontent yo'q.", show_alert=True)
        return

    buttons = [[InlineKeyboardButton(text=f"✏️ {i.title}", callback_data=f"admin:editpick:{i.id}:{content_type}")] for i in items]
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admin:type:{content_type}")])
    await callback.message.edit_text("Tahrirlamoqchi bo'lgan kontentni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:editpick:"))
async def admin_edit_pick(callback: CallbackQuery) -> None:
    _, _, content_id, content_type = callback.data.split(":")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Nomi", callback_data=f"admin:editfield:title:{content_id}:{content_type}")],
            [InlineKeyboardButton(text="📝 Tavsifi", callback_data=f"admin:editfield:description:{content_id}:{content_type}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admin:editmenu:{content_type}")],
        ]
    )
    await callback.message.edit_text("Qaysi maydonni tahrirlaysiz?", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:editfield:"))
async def admin_edit_field_start(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, field, content_id, content_type = callback.data.split(":")
    await state.set_state(AdminContentStates.waiting_edit_value)
    await state.update_data(field=field, content_id=int(content_id), content_type=content_type)
    await callback.message.answer("✏️ Yangi qiymatni yozing:")
    await callback.answer()


@router.message(AdminContentStates.waiting_edit_value, F.text)
async def admin_edit_value_received(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await update_content_field(session, data["content_id"], data["field"], message.text.strip())
    await state.clear()
    await message.answer("✅ Yangilandi!")


# ---------- Ro'yxat ----------

@router.callback_query(F.data.startswith("admin:listview:"))
async def admin_list_view(callback: CallbackQuery, session: AsyncSession) -> None:
    content_type = callback.data.split(":")[2]
    items = await get_content_list(session, content_type)
    label = TYPE_LABELS.get(content_type, content_type)

    if not items:
        text = f"{label}\n\n📭 Hozircha kontent yo'q."
    else:
        lines = [f"#{i.id} — {i.title}" for i in items]
        text = f"{label} ro'yxati:\n\n" + "\n".join(lines)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admin:type:{content_type}")]])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
