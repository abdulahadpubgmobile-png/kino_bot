import math
from typing import List, Optional
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from app.database.models import Movie

MOVIES_PER_PAGE = 5


def movie_keyboard(movie: Movie) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if movie.trailer_url:
        kb.button(text="🎥 Trailer", url=movie.trailer_url)
    kb.button(text="📤 Ulashish", switch_inline_query=f"kino_{movie.code}")
    kb.button(text="👁 Ko'rishlar: " + str(movie.views), callback_data="views_info")
    kb.adjust(2, 1)
    return kb.as_markup()


def movies_list_keyboard(
    movies: List[Movie],
    total: int,
    page: int,
    prefix: str = "page",
    extra: str = "",
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for movie in movies:
        kb.button(text=f"🎬 {movie.title} ({movie.year or '?'})", callback_data=f"movie_{movie.id}")
    kb.adjust(1)

    total_pages = math.ceil(total / MOVIES_PER_PAGE) if total else 1
    nav_buttons = []
    if page > 1:
        nav_buttons.append(("⬅️ Oldingi", f"{prefix}_{page - 1}_{extra}"))
    if page < total_pages:
        nav_buttons.append(("➡️ Keyingi", f"{prefix}_{page + 1}_{extra}"))

    if nav_buttons:
        for text, data in nav_buttons:
            kb.button(text=text, callback_data=data)
        kb.adjust(1, *([len(nav_buttons)]))

    kb.button(text=f"📄 {page}/{total_pages}", callback_data="page_info")
    kb.adjust(1)
    return kb.as_markup()


def genres_keyboard(genres: List[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for genre in genres:
        kb.button(text=f"🎭 {genre}", callback_data=f"genre_{genre}")
    kb.adjust(2)
    return kb.as_markup()


def confirm_keyboard(prefix: str = "confirm") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Saqlash", callback_data=f"{prefix}_yes")
    kb.button(text="✏️ Tahrirlash", callback_data=f"{prefix}_edit")
    kb.button(text="❌ Bekor qilish", callback_data=f"{prefix}_no")
    kb.adjust(2, 1)
    return kb.as_markup()


def subscribe_check_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tekshirish", callback_data="check_subscribe")
    return kb.as_markup()


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🎬 Kino qo'shish", callback_data="admin_add_movie")
    kb.button(text="📊 Statistika", callback_data="admin_stats")
    kb.button(text="📢 Broadcast", callback_data="admin_broadcast")
    kb.button(text="🗂 Barcha kinolar", callback_data="admin_movies_1")
    kb.button(text="📡 Kanallar", callback_data="admin_channels")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Yuborish", callback_data="broadcast_confirm")
    kb.button(text="❌ Bekor", callback_data="broadcast_cancel")
    kb.adjust(2)
    return kb.as_markup()


def back_keyboard(callback_data: str = "back_main") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Orqaga", callback_data=callback_data)
    return kb.as_markup()
