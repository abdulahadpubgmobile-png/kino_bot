from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters import IsAdmin
from app.states import AddMovieFSM
from app.database.queries.movies import add_movie, get_movie_by_code
from app.keyboards.reply import cancel_keyboard, skip_keyboard, main_keyboard
from app.keyboards.inline import confirm_keyboard

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# Barcha AddMovieFSM state'larida "❌ Bekor qilish" ishlashi uchun
CANCEL_TEXT = "❌ Bekor qilish"


@router.callback_query(F.data == "admin_add_movie")
async def add_movie_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()  # avvalgi state'ni tozala
    await state.set_state(AddMovieFSM.waiting_for_code)
    await callback.message.answer(
        "📌 <b>Kino qo'shish</b>\n\n"
        "1-qadam: Kino kodini yuboring (masalan: <code>001</code>):",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


# Barcha state'larda ishlaydi — eng muhim fix
@router.message(AddMovieFSM.waiting_for_code, F.text == CANCEL_TEXT)
@router.message(AddMovieFSM.waiting_for_title, F.text == CANCEL_TEXT)
@router.message(AddMovieFSM.waiting_for_year, F.text == CANCEL_TEXT)
@router.message(AddMovieFSM.waiting_for_country, F.text == CANCEL_TEXT)
@router.message(AddMovieFSM.waiting_for_genre, F.text == CANCEL_TEXT)
@router.message(AddMovieFSM.waiting_for_description, F.text == CANCEL_TEXT)
@router.message(AddMovieFSM.waiting_for_trailer, F.text == CANCEL_TEXT)
@router.message(AddMovieFSM.waiting_for_video, F.text == CANCEL_TEXT)
@router.message(AddMovieFSM.waiting_for_poster, F.text == CANCEL_TEXT)
async def cancel_fsm(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Kino qo'shish bekor qilindi.", reply_markup=main_keyboard())


@router.message(AddMovieFSM.waiting_for_code)
async def get_code(message: Message, state: FSMContext, session: AsyncSession) -> None:
    code = message.text.strip()
    existing = await get_movie_by_code(session, code)
    if existing:
        await message.answer(
            f"⚠️ <b>{code}</b> kodi allaqachon mavjud! Boshqa kod kiriting:",
            parse_mode="HTML"
        )
        return
    await state.update_data(code=code)
    await state.set_state(AddMovieFSM.waiting_for_title)
    await message.answer("🎬 2-qadam: Kino nomini yuboring:", reply_markup=cancel_keyboard())


@router.message(AddMovieFSM.waiting_for_title)
async def get_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovieFSM.waiting_for_year)
    await message.answer(
        "📅 3-qadam: Kino yilini yuboring (masalan: <code>2023</code>):",
        parse_mode="HTML",
        reply_markup=skip_keyboard()
    )


@router.message(AddMovieFSM.waiting_for_year)
async def get_year(message: Message, state: FSMContext) -> None:
    year = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(year=year)
    await state.set_state(AddMovieFSM.waiting_for_country)
    await message.answer("🌍 4-qadam: Davlatni yuboring:", reply_markup=skip_keyboard())


@router.message(AddMovieFSM.waiting_for_country)
async def get_country(message: Message, state: FSMContext) -> None:
    country = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(country=country)
    await state.set_state(AddMovieFSM.waiting_for_genre)
    await message.answer(
        "🎭 5-qadam: Janrni yuboring (masalan: <code>Drama, Komediya</code>):",
        parse_mode="HTML",
        reply_markup=skip_keyboard()
    )


@router.message(AddMovieFSM.waiting_for_genre)
async def get_genre(message: Message, state: FSMContext) -> None:
    genre = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(genre=genre)
    await state.set_state(AddMovieFSM.waiting_for_description)
    await message.answer("📝 6-qadam: Tavsif yuboring:", reply_markup=skip_keyboard())


@router.message(AddMovieFSM.waiting_for_description)
async def get_description(message: Message, state: FSMContext) -> None:
    desc = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AddMovieFSM.waiting_for_trailer)
    await message.answer("🎥 7-qadam: Trailer URL yuboring:", reply_markup=skip_keyboard())


@router.message(AddMovieFSM.waiting_for_trailer)
async def get_trailer(message: Message, state: FSMContext) -> None:
    trailer = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(trailer_url=trailer)
    await state.set_state(AddMovieFSM.waiting_for_video)
    await message.answer("📹 8-qadam: Kino videosini yuboring:", reply_markup=cancel_keyboard())


@router.message(AddMovieFSM.waiting_for_video, F.video)
async def get_video(message: Message, state: FSMContext) -> None:
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AddMovieFSM.waiting_for_poster)
    await message.answer("🖼 9-qadam: Poster (rasm) yuboring:", reply_markup=skip_keyboard())


@router.message(AddMovieFSM.waiting_for_video)
async def get_video_invalid(message: Message) -> None:
    await message.answer("⚠️ Iltimos, video fayl yuboring!")


@router.message(AddMovieFSM.waiting_for_poster, F.photo)
async def get_poster(message: Message, state: FSMContext) -> None:
    await state.update_data(poster_file_id=message.photo[-1].file_id)
    await show_confirm(message, state)


@router.message(AddMovieFSM.waiting_for_poster, F.text == "⏭ O'tkazib yuborish")
async def get_poster_skip(message: Message, state: FSMContext) -> None:
    await state.update_data(poster_file_id=None)
    await show_confirm(message, state)


@router.message(AddMovieFSM.waiting_for_poster)
async def get_poster_invalid(message: Message) -> None:
    await message.answer("⚠️ Rasm yuboring yoki o'tkazib yuboring!")


async def show_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(AddMovieFSM.waiting_for_confirm)
    preview = (
        f"🎬 <b>{data.get('title')}</b>\n\n"
        f"📌 Kod: <code>{data.get('code')}</code>\n"
        f"📅 Yil: {data.get('year') or '—'}\n"
        f"🌍 Davlat: {data.get('country') or '—'}\n"
        f"🎭 Janr: {data.get('genre') or '—'}\n"
        f"📝 {data.get('description') or '—'}\n\n"
        f"❓ <b>Saqlaymizmi?</b>"
    )
    await message.answer(preview, reply_markup=confirm_keyboard("movie_confirm"), parse_mode="HTML")


@router.callback_query(AddMovieFSM.waiting_for_confirm, F.data == "movie_confirm_yes")
async def confirm_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await state.clear()
    movie = await add_movie(
        session,
        code=data["code"],
        title=data["title"],
        year=data.get("year"),
        country=data.get("country"),
        genre=data.get("genre"),
        description=data.get("description"),
        trailer_url=data.get("trailer_url"),
        file_id=data["file_id"],
        poster_file_id=data.get("poster_file_id"),
    )
    await callback.message.edit_text(
        f"✅ <b>{movie.title}</b> kinosi qo'shildi!\n📌 Kod: <code>{movie.code}</code>",
        parse_mode="HTML",
    )
    await callback.answer("✅ Saqlandi!")


@router.callback_query(AddMovieFSM.waiting_for_confirm, F.data == "movie_confirm_edit")
async def confirm_edit(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AddMovieFSM.waiting_for_code)
    await callback.message.answer(
        "✏️ Qaytadan boshlaylik.\n\n1-qadam: Kino kodini yuboring:",
        reply_markup=cancel_keyboard()
    )
    await callback.answer()


@router.callback_query(AddMovieFSM.waiting_for_confirm, F.data == "movie_confirm_no")
async def confirm_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.answer()
