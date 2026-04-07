import os
import tempfile

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup
from sqlalchemy import select

from config import conf
from keyboards.inline import (
    channel_application_kb,
    homework_done_kb,
    review_kb,
    vacancies_kb,
    vacancy_view_detail_kb,
    vacancy_view_list_kb,
)
from models.bot_user import BotUser
from models.database import db
from models.question import Question
from models.vacancy import Vacancy
from services.pdf import build_application_pdf

router = Router(name="user")

USER_BTN_APPLY = "📋 Ariza qoldirish"
USER_BTN_VIEW  = "🔍 Vakansiyalarni ko'rish"
USER_BTN_AI    = "🤖 AI yordamchi"
USER_BTN_FAQ   = "📋 Tez-tez so'raladigan savollar"


class UserForm(StatesGroup):
    answering = State()


class HomeworkStates(StatesGroup):
    collecting = State()


class ReviewState(StatesGroup):
    waiting = State()


# ─────────────────────────── helpers ────────────────────────────────

def _main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=USER_BTN_VIEW),  KeyboardButton(text=USER_BTN_APPLY)],
            [KeyboardButton(text=USER_BTN_FAQ)],
            [KeyboardButton(text=USER_BTN_AI)],
        ],
        resize_keyboard=True,
    )


async def _ensure_user(message: Message) -> None:
    if not message.from_user:
        return
    uid = message.from_user.id
    r = await db.execute(select(BotUser).where(BotUser.telegram_id == uid))
    if r.scalar_one_or_none():
        return
    await BotUser.create(
        telegram_id=uid,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )


async def _load_questions(vacancy_id: int) -> list[Question]:
    r = await db.execute(
        select(Question)
        .where(Question.vacancy_id == vacancy_id)
        .order_by(Question.sort_order, Question.id)
    )
    return list(r.scalars().all())


async def _ask_current(target: Message | CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    questions = data["questions"]
    idx = data["idx"]
    chat_id = target.chat.id if isinstance(target, Message) else target.message.chat.id
    bot = target.bot

    if idx >= len(questions):
        await _finalize(bot, state, chat_id, target.from_user)
        return

    q = questions[idx]
    n = len(questions)
    text = f"❓ <b>{idx + 1} / {n}</b>\n\n{q['text']}"
    if q["require_photo"]:
        text += "\n\n📷 Rasm yuboring (izoh ixtiyoriy)."
    else:
        text += "\n\n✍️ Javobni matn bilan yozing."

    if isinstance(target, Message):
        await target.answer(text)
    else:
        await target.message.answer(text)


async def _finalize(bot, state: FSMContext, chat_id: int, from_user) -> None:
    data = await state.get_data()
    await state.clear()

    vacancy_title = data.get("vacancy_title", "")
    answers = data.get("answers", [])
    questions = data.get("questions", [])

    qmeta = {q["id"]: q for q in questions}
    items: list[dict] = []
    temp_photo_files: list[str] = []

    for a in answers:
        qid = a["question_id"]
        meta = qmeta.get(qid, {})
        items.append({
            "question": meta.get("text") or "",
            "answer_text": a.get("text") or None,
            "image_path": a.get("photo_path"),
            "require_photo": bool(meta.get("require_photo")),
        })
        if a.get("photo_path"):
            temp_photo_files.append(a["photo_path"])

    label_parts = []
    if from_user:
        if from_user.username:
            label_parts.append(f"@{from_user.username}")
        if from_user.full_name:
            label_parts.append(from_user.full_name)
        label_parts.append(f"id:{from_user.id}")
    applicant_label = " ".join(label_parts) if label_parts else str(chat_id)

    try:
        pdf_path = build_application_pdf(
            vacancy_title=vacancy_title,
            applicant_label=applicant_label,
            items=items,
        )
    except Exception:
        for item in items:
            item["image_path"] = None
        pdf_path = build_application_pdf(
            vacancy_title=vacancy_title,
            applicant_label=applicant_label,
            items=items,
        )

    # Clean up temp photo files (PDF kept alive for review step)
    for p in temp_photo_files:
        try:
            os.unlink(p)
        except OSError:
            pass

    # Send PDF to user for review
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    doc = BufferedInputFile(pdf_bytes, filename="zayavka.pdf")

    uid = from_user.id if from_user else chat_id

    await state.set_state(ReviewState.waiting)
    await state.update_data(
        pdf_path=pdf_path,
        vacancy_title=vacancy_title,
        applicant_label=applicant_label,
        applicant_uid=uid,
    )

    await bot.send_document(
        chat_id,
        doc,
        caption=(
            "📄 <b>Arizangiz tayyor!</b>\n\n"
            "Ma'lumotlarni tekshirib ko'ring.\n"
            "Hammasi to'g'rimi?"
        ),
        reply_markup=review_kb(),
    )


def _cleanup_pdf(pdf_path: str | None) -> None:
    if pdf_path:
        try:
            os.unlink(pdf_path)
        except OSError:
            pass


# ─────────────────────────── Review callbacks ───────────────────────

@router.callback_query(F.data == "rev:ok", ReviewState.waiting)
async def review_confirm(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    data = await state.get_data()
    pdf_path: str | None = data.get("pdf_path")
    vacancy_title: str = data.get("vacancy_title", "")
    applicant_label: str = data.get("applicant_label", "")
    uid: int = data.get("applicant_uid", query.from_user.id if query.from_user else 0)
    await state.clear()

    target = conf.bot.target_chat_id
    if target and pdf_path and os.path.isfile(pdf_path):
        try:
            target_id: int | str = int(target)
        except ValueError:
            target_id = target
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        cap = f"🆕 Yangi ariza: {vacancy_title}\n{applicant_label}"
        doc = BufferedInputFile(pdf_bytes, filename="zayavka.pdf")
        try:
            await query.bot.send_document(
                target_id,
                doc,
                caption=cap[:1024],
                reply_markup=channel_application_kb(uid),
            )
        except Exception:
            pass

    _cleanup_pdf(pdf_path)

    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    await query.message.answer(
        "✅ <b>Arizangiz yuborildi!</b>\n\n"
        "Tez orada siz bilan bog'lanamiz. 🙌",
        reply_markup=_main_kb(),
    )


@router.callback_query(F.data == "rev:redo", ReviewState.waiting)
async def review_redo(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    data = await state.get_data()
    _cleanup_pdf(data.get("pdf_path"))
    await state.clear()

    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    await query.message.answer(
        "🔄 Ariza bekor qilindi.\n"
        "Qaytadan boshlash uchun «📋 Ariza qoldirish» tugmasini bosing.",
        reply_markup=_main_kb(),
    )


# ─────────────────────────── /start ─────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _ensure_user(message)
    await message.answer(
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Bu yerda ishga <b>ariza</b> qoldirishingiz yoki "
        "<b>vakansiyalar</b> bilan tanishishingiz mumkin.\n\n"
        "Quyidagi tugmalardan birini tanlang 👇",
        reply_markup=_main_kb(),
    )


# ─────────────────────────── Vacancy view (client) ──────────────────

@router.message(F.text == USER_BTN_VIEW)
async def menu_view_vacancies(message: Message, state: FSMContext) -> None:
    await state.clear()
    r = await db.execute(
        select(Vacancy)
        .where(Vacancy.is_active.is_(True))
        .order_by(Vacancy.sort_order, Vacancy.id)
    )
    vacs = list(r.scalars().all())
    if not vacs:
        await message.answer(
            "📭 Hozircha faol vakansiya yo'q. Keyinroq urinib ko'ring.",
            reply_markup=_main_kb(),
        )
        return
    await message.answer(
        "🔍 <b>Mavjud vakansiyalar:</b>\n\nBatafsil ko'rish uchun tanlang 👇",
        reply_markup=vacancy_view_list_kb(vacs),
    )


@router.callback_query(F.data.startswith("vview:"))
async def cb_vacancy_view(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    raw = query.data or ""

    if raw == "vview:back":
        try:
            await query.message.delete()
        except TelegramBadRequest:
            pass
        return

    try:
        vid = int(raw.split(":", 1)[1])
    except (ValueError, IndexError):
        return

    v = await Vacancy.get_or_none(vid)
    if not v or not v.is_active:
        await query.message.answer("⚠️ Vakansiya mavjud emas.")
        return

    qs = await _load_questions(vid)
    desc = v.description or "Tavsif qo'shilmagan."
    text = (
        f"💼 <b>{v.title}</b>\n\n"
        f"📄 {desc}\n\n"
        f"❓ Savollar soni: {len(qs)} ta"
    )
    try:
        await query.message.edit_text(text, reply_markup=vacancy_view_detail_kb(vid))
    except TelegramBadRequest:
        await query.message.answer(text, reply_markup=vacancy_view_detail_kb(vid))


# ─────────────────────────── Apply ──────────────────────────────────

@router.message(F.text == USER_BTN_APPLY)
async def menu_apply(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _ensure_user(message)
    r = await db.execute(
        select(Vacancy)
        .where(Vacancy.is_active.is_(True))
        .order_by(Vacancy.sort_order, Vacancy.id)
    )
    vacs = list(r.scalars().all())
    if not vacs:
        await message.answer(
            "📭 Hozircha faol vakansiya yo'q. Keyinroq urinib ko'ring.",
            reply_markup=_main_kb(),
        )
        return
    await message.answer("💼 Vakansiyani tanlang:", reply_markup=vacancies_kb(vacs))


@router.callback_query(F.data.startswith("vac:"))
async def cb_vacancy_pick(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    raw = query.data or ""
    if raw == "vac:cancel":
        await state.clear()
        try:
            await query.message.delete()
        except TelegramBadRequest:
            pass
        return

    try:
        vid = int(raw.split(":", 1)[1])
    except (ValueError, IndexError):
        return

    v = await Vacancy.get_or_none(vid)
    if not v or not v.is_active:
        await query.message.answer("⚠️ Vakansiya mavjud emas.")
        return

    qs = await _load_questions(vid)
    if not qs:
        await query.message.answer(
            "⚠️ Bu vakansiya uchun hozircha savollar yo'q. Administrator bilan bog'laning."
        )
        return

    questions = [{"id": q.id, "text": q.text, "require_photo": q.require_photo} for q in qs]
    await state.set_state(UserForm.answering)
    await state.update_data(
        vacancy_id=vid,
        vacancy_title=v.title,
        questions=questions,
        idx=0,
        answers=[],
    )
    try:
        await query.message.edit_text(f"💼 <b>{v.title}</b>\n\n📝 Anketani boshlaymiz.")
    except TelegramBadRequest:
        await query.message.answer(f"💼 <b>{v.title}</b>\n\n📝 Anketani boshlaymiz.")
    await _ask_current(query, state)


# ─────────────────────────── Answering form ─────────────────────────

@router.message(UserForm.answering, F.text)
async def answer_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    questions = data.get("questions") or []
    idx = data.get("idx", 0)
    if idx >= len(questions):
        await state.clear()
        return
    q = questions[idx]
    if q["require_photo"]:
        await message.answer("📷 Bu savol uchun rasm yuborishingiz kerak (izoh ixtiyoriy).")
        return
    answers = data.get("answers") or []
    answers.append({"question_id": q["id"], "text": message.text.strip(), "photo_path": None})
    await state.update_data(idx=idx + 1, answers=answers)
    await _ask_current(message, state)


@router.message(UserForm.answering, F.photo)
async def answer_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    questions = data.get("questions") or []
    idx = data.get("idx", 0)
    if idx >= len(questions):
        await state.clear()
        return
    q = questions[idx]
    if not q["require_photo"]:
        await message.answer("✍️ Bu savol uchun faqat matn kerak (rasm emas).")
        return

    photo = message.photo[-1]
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    f = await message.bot.get_file(photo.file_id)
    await message.bot.download_file(f.file_path, path)

    caption = (message.caption or "").strip()
    answers = data.get("answers") or []
    answers.append({"question_id": q["id"], "text": caption, "photo_path": path})
    await state.update_data(idx=idx + 1, answers=answers)
    await _ask_current(message, state)


@router.message(UserForm.answering)
async def answer_invalid(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    questions = data.get("questions") or []
    idx = data.get("idx", 0)
    if idx >= len(questions):
        return
    q = questions[idx]
    if q["require_photo"]:
        await message.answer("📷 Rasm yuboring (izoh bilan ham bo'lishi mumkin).")
    else:
        await message.answer("✍️ Matnli javob yuboring.")


# ─────────────────────────── Homework ───────────────────────────────

@router.callback_query(F.data == "hw:go")
async def homework_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.set_state(HomeworkStates.collecting)
    await state.update_data(hw_items=[])
    await query.message.answer(
        "📤 Bajarilgan vazifani yuboring: matn, fayl, rasm yoki video.\n"
        "✅ Hammasi tayyor bo'lsa — «Tayyor» tugmasini bosing.\n\n"
        "⛔️ Bekor: /cancel",
        reply_markup=homework_done_kb(),
    )


@router.callback_query(F.data == "hw:done")
async def homework_done(query: CallbackQuery, state: FSMContext) -> None:
    cur = await state.get_state()
    if cur != HomeworkStates.collecting.state:
        await query.answer("Avvalo «Vazifani yuborish» tugmasini bosing.", show_alert=True)
        return

    await query.answer("✅ Qabul qilindi")
    data = await state.get_data()
    items: list = data.get("hw_items") or []
    await state.clear()
    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    n = len(items)
    await query.message.answer(
        f"🎉 Rahmat! Qabul qilingan materiallar: {n} ta.",
        reply_markup=_main_kb(),
    )
    uname = f"@{query.from_user.username}" if query.from_user and query.from_user.username else "—"
    uid = query.from_user.id if query.from_user else 0
    for aid in conf.bot.admin_ids:
        try:
            await query.bot.send_message(
                aid,
                f"📥 Vazifa topshirildi: foydalanuvchi {uid} {uname}. Materiallar: {n} ta.",
            )
        except Exception:
            pass


@router.message(Command("cancel"), HomeworkStates.collecting)
async def homework_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Vazifa qabul qilish bekor qilindi.", reply_markup=_main_kb())


@router.message(HomeworkStates.collecting)
async def homework_collect(message: Message, state: FSMContext) -> None:
    if message.text and message.text.startswith("/"):
        await message.answer("⛔️ Bekor qilish uchun /cancel yuboring.")
        return
    data = await state.get_data()
    items: list = list(data.get("hw_items") or [])
    if message.text:
        items.append({"kind": "text", "text": message.text[:4000]})
    elif message.document:
        items.append({"kind": "doc", "file_id": message.document.file_id, "name": message.document.file_name or "file"})
    elif message.photo:
        items.append({"kind": "photo", "file_id": message.photo[-1].file_id})
    elif message.video:
        items.append({"kind": "video", "file_id": message.video.file_id})
    elif message.voice:
        items.append({"kind": "voice", "file_id": message.voice.file_id})
    elif message.audio:
        items.append({"kind": "audio", "file_id": message.audio.file_id})
    else:
        await message.answer("📎 Matn, rasm, hujjat, audio yoki video yuboring.")
        return
    await state.update_data(hw_items=items)
    await message.answer(f"✅ Saqlandi ({len(items)} ta). Yana yuborishingiz yoki «Tayyor» tugmasini bosing.")
