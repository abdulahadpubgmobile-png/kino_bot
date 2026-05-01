import math
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.queries.movies import (
    get_movie_by_code, get_movie_by_id, increment_views,
    search_movies, get_movies_by_genre, get_all_movies,
    get_all_genres, MOVIES_PER_PAGE,
)
from app.keyboards.inline import (
    movie_keyboard, movies_list_keyboard, genres_keyboard, back_keyboard
)
from app.keyboards.reply import main_keyboard, cancel_keyboard
from app.states import SearchFSM

router = Router()

SKIP = ("🎬 Kinolar", "🔍 Qidirish", "🎭 Janrlar", "ℹ️ Yordam", "❌ Bekor qilish")


def movie_caption(movie) -> str:
    return (
        f"🎬 <b>{movie.title}</b>\n\n"
        f"📅 Yil: {movie.year or '—'}\n"
        f"🌍 Davlat: {movie.country or '—'}\n"
        f"🎭 Janr: {movie.genre or '—'}\n"
        f"👁 Ko'rishlar: {movie.views}\n\n"
        f"📝 {movie.description or ''}"
    )


async def send_movie(message_or_callback, movie, session: AsyncSession) -> None:
    await increment_views(session, movie.id)
    caption = movie_caption(movie)
    kb = movie_keyboard(movie)

    if isinstance(message_or_callback, Message):
        send = message_or_callback
    else:
        send = message_or_callback.message

    if movie.poster_file_id:
        await send.answer_photo(
            photo=movie.poster_file_id,
            caption=caption,
            reply_markup=kb,
            parse_mode="HTML",
        )
    else:
        await send.answer(caption, reply_markup=kb, parse_mode="HTML")

    await send.answer_video(
        video=movie.file_id,
        caption=f"🎬 {movie.title}",
    )


# Kod orqali kino olish
@router.message(F.text & ~F.text.in_(SKIP), StateFilter(None))
async def get_movie_by_code_handler(message: Message, session: AsyncSession, state: FSMContext) -> None:
    code = message.text.strip()
    movie = await get_movie_by_code(session, code)
    if movie:
        await send_movie(message, movie, session)
    else:
        await message.answer(
            f"🔍 <b>{code}</b> kodli kino topilmadi.\n"
            "Qidiruv uchun 🔍 Qidirish tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )


# Barcha kinolar ro'yxati
@router.message(F.text == "🎬 Kinolar")
async def all_movies_handler(message: Message, session: AsyncSession) -> None:
    movies, total = await get_all_movies(session, page=1)
    if not movies:
        await message.answer("🎬 Hozircha kinolar mavjud emas.")
        return

    total_pages = math.ceil(total / MOVIES_PER_PAGE)
    await message.answer(
        f"🎬 <b>Barcha kinolar</b> ({total} ta)\n\nKinoni tanlang:",
        reply_markup=movies_list_keyboard(movies, total, 1, prefix="all_page"),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("all_page_"))
async def all_movies_page_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split("_")
    page = int(parts[2])
    movies, total = await get_all_movies(session, page=page)
    total_pages = math.ceil(total / MOVIES_PER_PAGE) if total else 1

    await callback.message.edit_text(
        f"🎬 <b>Barcha kinolar</b> ({total} ta)\n\nKinoni tanlang:",
        reply_markup=movies_list_keyboard(movies, total, page, prefix="all_page"),
        parse_mode="HTML",
    )
    await callback.answer()


# Kino callback
@router.callback_query(F.data.startswith("movie_"))
async def movie_detail_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    movie_id = int(callback.data.split("_")[1])
    movie = await get_movie_by_id(session, movie_id)
    if not movie:
        await callback.answer("❌ Kino topilmadi!", show_alert=True)
        return
    await send_movie(callback, movie, session)
    await callback.answer()


# Qidirish FSM
@router.message(F.text == "🔍 Qidirish")
async def search_start_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(SearchFSM.waiting_for_query)
    await message.answer(
        "🔍 <b>Qidiruv</b>\n\nKino nomi yoki kodini yozing:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )


@router.message(SearchFSM.waiting_for_query, F.text == "❌ Bekor qilish")
async def search_cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Qidiruv bekor qilindi.", reply_markup=main_keyboard())


@router.message(SearchFSM.waiting_for_query)
async def search_query_handler(message: Message, session: AsyncSession, state: FSMContext) -> None:
    query = message.text.strip()
    await state.clear()

    movies, total = await search_movies(session, query, page=1)
    if not movies:
        await message.answer(
            f"😔 <b>{query}</b> bo'yicha hech narsa topilmadi.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    await message.answer(
        f"🔍 <b>{query}</b> bo'yicha natijalar ({total} ta):",
        reply_markup=movies_list_keyboard(movies, total, 1, prefix="search_page", extra=query),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("search_page_"))
async def search_page_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split("_", 3)
    page = int(parts[2])
    query = parts[3] if len(parts) > 3 else ""

    movies, total = await search_movies(session, query, page=page)
    await callback.message.edit_text(
        f"🔍 <b>{query}</b> bo'yicha natijalar ({total} ta):",
        reply_markup=movies_list_keyboard(movies, total, page, prefix="search_page", extra=query),
        parse_mode="HTML",
    )
    await callback.answer()


# Janrlar
@router.message(F.text == "🎭 Janrlar")
async def genres_handler(message: Message, session: AsyncSession) -> None:
    genres = await get_all_genres(session)
    if not genres:
        await message.answer("🎭 Hozircha janrlar mavjud emas.")
        return
    await message.answer(
        "🎭 <b>Janrlar</b>\n\nQaysi janrni ko'rmoqchisiz?",
        reply_markup=genres_keyboard(genres),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("genre_"))
async def genre_movies_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    genre = callback.data[6:]
    movies, total = await get_movies_by_genre(session, genre, page=1)

    if not movies:
        await callback.answer(f"😔 {genre} janrida kinolar topilmadi.", show_alert=True)
        return

    await callback.message.edit_text(
        f"🎭 <b>{genre}</b> janridagi kinolar ({total} ta):",
        reply_markup=movies_list_keyboard(movies, total, 1, prefix="genre_page", extra=genre),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("genre_page_"))
async def genre_page_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split("_", 3)
    page = int(parts[2])
    genre = parts[3] if len(parts) > 3 else ""

    movies, total = await get_movies_by_genre(session, genre, page=page)
    await callback.message.edit_text(
        f"🎭 <b>{genre}</b> janridagi kinolar ({total} ta):",
        reply_markup=movies_list_keyboard(movies, total, page, prefix="genre_page", extra=genre),
        parse_mode="HTML",
    )
    await callback.answer()
