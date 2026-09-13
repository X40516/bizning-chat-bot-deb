"""
Doimiy (Reply) klaviaturalar.
"""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

MAIN_MENU_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💕 Sevishganlar uchun")],
        [KeyboardButton(text="💬 Bizning chat")],
    ],
    resize_keyboard=True,
)

BACK_ONLY_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="⬅️ Orqaga")]],
    resize_keyboard=True,
)
