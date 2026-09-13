"""
💕 Sevishganlar uchun - kino, musiqa, rasm va videolarni ko'rish.
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.queries import get_content_by_id, get_content_list

router = Router(name="content")

TYPE_LABELS = {
    "movie": "🎬 Kino",
    "music": "🎵 Music",
    "photo": "🖼️ Rasmlar",
    "video": "🎥 Videolar",
}


def _love_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Kino", callback_data="love:list:movie")],
            [InlineKeyboardButton(text="🎵 Music", callback_data="love:list:music")],
            [InlineKeyboardButton(text="🖼️ Rasmlar", callback_data="love:list:photo")],
            [InlineKeyboardButton(text="🎥 Videolar", callback_data="love:list:video")],
        ]
    )


@router.message(F.text == "💕 Sevishganlar uchun")
async def love_menu(message: Message) -> None:
    await message.answer("💕 Sevishganlar uchun bo'lim tanlang:", reply_markup=_love_menu_kb())


@router.callback_query(F.data == "love:menu")
async def love_menu_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text("💕 Sevishganlar uchun bo'lim tanlang:", reply_markup=_love_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("love:list:"))
async def love_list(callback: CallbackQuery, session: AsyncSession) -> None:
    content_type = callback.data.split(":")[2]
    items = await get_content_list(session, content_type)
    label = TYPE_LABELS.get(content_type, content_type)

    if not items:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="love:menu")]])
        await callback.message.edit_text(f"{label}\n\n📭 Hozircha kontent yo'q.", reply_markup=kb)
        await callback.answer()
        return

    buttons = [[InlineKeyboardButton(text=item.title, callback_data=f"love:show:{item.id}")] for item in items]
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="love:menu")])
    await callback.message.edit_text(f"{label} ro'yxati:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("love:show:"))
async def love_show(callback: CallbackQuery, session: AsyncSession) -> None:
    content_id = int(callback.data.split(":")[2])
    item = await get_content_by_id(session, content_id)
    if item is None:
        await callback.answer("❌ Topilmadi.", show_alert=True)
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"love:list:{item.type}")]]
    )

    caption_parts = [item.title]
    if item.artist:
        caption_parts.append(f"🎤 {item.artist}")
    if item.genre:
        caption_parts.append(f"🏷️ {item.genre}")
    if item.description:
        caption_parts.append(item.description)
    caption = "\n".join(caption_parts)

    try:
        if item.type == "movie" or item.type == "video":
            await callback.message.answer_video(item.telegram_file_id, caption=caption, reply_markup=kb)
        elif item.type == "music":
            await callback.message.answer_audio(item.telegram_file_id, caption=caption, reply_markup=kb)
        elif item.type == "photo":
            await callback.message.answer_photo(item.telegram_file_id, caption=caption, reply_markup=kb)
        else:
            await callback.message.answer(caption, reply_markup=kb)
    except Exception:
        await callback.message.answer("❌ Kontentni yuklashda xatolik yuz berdi.", reply_markup=kb)

    await callback.answer()
