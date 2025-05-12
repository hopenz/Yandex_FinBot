from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

CATEGORIES = ["Продукты", "Транспорт", "Жильё", "Развлечения", "Другое"]

def category_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat, callback_data=f"cat:{cat}")]
            for cat in CATEGORIES
        ]
    )