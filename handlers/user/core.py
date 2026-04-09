import asyncio
import os

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    KeyboardButton,
    ReplyKeyboardRemove,
    Message,
    ReplyKeyboardMarkup,
)
from sqlalchemy import select

from config import conf
from keyboards.inline import (
    channel_application_kb,
    hr_city_kb,
    hr_pd_consent_kb,
    hr_test_choice_kb,
    language_pick_kb,
    vacancies_kb,
    vacancy_view_detail_kb,
    vacancy_view_list_kb,
)
from locales.messages import LANG_UZ, all_labels, main_menu_kb, msg, norm_lang, pick_language_prompt
from models.database import db
from models.question import Question
from models.vacancy import Vacancy
from services.pdf import build_application_pdf, build_candidate_compact_pdf
from utils.user_locale import ensure_bot_user, get_user_locale, set_user_locale

router = Router(name="user")


class UserForm(StatesGroup):
    answering = State()


class PostFormState(StatesGroup):
    waiting_resume = State()
    waiting_test_submit = State()


class ReviewState(StatesGroup):
    waiting = State()


class HRCandidateState(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_city = State()
    waiting_resume = State()
    waiting_portfolio = State()
    waiting_custom_answer = State()
    waiting_test_choice = State()
    waiting_test_submit = State()


_reminder_tasks: dict[int, asyncio.Task] = {}


def _is_url(text: str | None) -> bool:
    if not text:
        return False
    t = text.strip().lower()
    return t.startswith("http://") or t.startswith("https://")


def _allowed_doc_name(filename: str | None) -> bool:
    if not filename:
        return False
    name = filename.lower()
    return name.endswith(".pdf") or name.endswith(".doc") or name.endswith(".docx")


def _phone_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=msg(lang, "hr_phone_btn"), request_contact=True)],
            [KeyboardButton(text=msg(lang, "btn_stop_form"), style="danger")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _stop_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=msg(lang, "btn_stop_form"), style="danger")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _cancel_reminder(user_id: int) -> None:
    task = _reminder_tasks.pop(user_id, None)
    if task and not task.done():
        task.cancel()


async def _schedule_reminder(user_id: int, chat_id: int, bot, lang: str) -> None:
    _cancel_reminder(user_id)

    async def _job() -> None:
        try:
            await asyncio.sleep(24 * 60 * 60)
            await bot.send_message(
                chat_id,
                f"⏰ {msg(lang, 'hr_test_waiting')}",
                reply_markup=hr_test_choice_kb(lang),
            )
        except asyncio.CancelledError:
            return
        finally:
            _reminder_tasks.pop(user_id, None)

    _reminder_tasks[user_id] = asyncio.create_task(_job())


def _main_kb(lang: str) -> ReplyKeyboardMarkup:
    """Для ai_chat и других модулей: главное меню по языку."""
    return main_menu_kb(lang)


async def _user_lang(telegram_id: int) -> str:
    loc = await get_user_locale(telegram_id)
    return norm_lang(loc) if loc else LANG_UZ


async def _require_language_or_hint(message: Message) -> str | None:
    """Если язык не выбран — показываем клавиатуру, возвращаем None."""
    if not message.from_user:
        return None
    loc = await get_user_locale(message.from_user.id)
    if not loc:
        await message.answer(pick_language_prompt(), reply_markup=language_pick_kb())
        return None
    return norm_lang(loc)


async def _load_questions(vacancy_id: int) -> list[Question]:
    r = await db.execute(
        select(Question)
        .where(Question.vacancy_id == vacancy_id)
        .order_by(Question.sort_order, Question.id)
    )
    return list(r.scalars().all())


def _bilingual_value(obj, lang: str, base: str) -> str | None:
    ru = getattr(obj, f"{base}_ru", None)
    uz = getattr(obj, f"{base}_uz", None)
    if norm_lang(lang) == "ru":
        return (ru or uz or getattr(obj, base, None))
    return (uz or ru or getattr(obj, base, None))


def _split_ru_uz(raw: str) -> tuple[str, str]:
    if "|" in raw:
        left, right = raw.split("|", 1)
        ru = left.strip()
        uz = right.strip()
        return (ru or uz), (uz or ru)
    text = raw.strip()
    return text, text


async def _ask_current(target: Message | CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    questions = data["questions"]
    idx = data["idx"]
    lang = data.get("ui_lang") or LANG_UZ
    chat_id = target.chat.id if isinstance(target, Message) else target.message.chat.id
    bot = target.bot

    if idx >= len(questions):
        await _ask_resume_after_form(bot, state, chat_id)
        return

    q = questions[idx]
    n = len(questions)
    text = f"❓ <b>{idx + 1} / {n}</b>\n\n{q['text']}"
    text += "\n\n" + msg(lang, "form_hint_text")
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=msg(lang, "btn_stop_form"))]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    if isinstance(target, Message):
        await target.answer(text, reply_markup=reply_markup)
    else:
        await target.message.answer(text, reply_markup=reply_markup)


async def _ask_resume_after_form(bot, state: FSMContext, chat_id: int) -> None:
    data = await state.get_data()
    lang = data.get("ui_lang") or LANG_UZ
    await state.set_state(PostFormState.waiting_resume)
    await bot.send_message(
        chat_id,
        msg(lang, "hr_resume_q"),
        reply_markup=_stop_kb(lang),
    )


async def _finalize_to_channel(bot, state: FSMContext, chat_id: int, from_user) -> None:
    data = await state.get_data()
    ui_lang = data.get("ui_lang") or LANG_UZ
    await state.clear()

    vacancy_title = data.get("vacancy_title", "")
    answers = data.get("answers", [])
    questions = data.get("questions", [])

    qmeta = {q["id"]: q for q in questions}
    items: list[dict] = []

    for a in answers:
        qid = a["question_id"]
        meta = qmeta.get(qid, {})
        items.append({
            "question": meta.get("text") or "",
            "answer_text": a.get("text") or None,
            "image_path": None,
            "require_photo": False,
        })

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


    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    doc = BufferedInputFile(pdf_bytes, filename="zayavka.pdf")

    uid = from_user.id if from_user else chat_id
    target = conf.bot.target_chat_id

    if target:
        try:
            target_id: int | str = int(target)
        except ValueError:
            target_id = target

        cap = msg(ui_lang, "channel_new_apply", title=vacancy_title, label=applicant_label)
        cap += "\n\n" + msg(ui_lang, "channel_interview_note")
        resume_text = data.get("resume_text")
        test_text = data.get("test_text")
        if resume_text:
            cap += f"\n\n📄 Resume: {resume_text}"
        if test_text:
            cap += f"\n🎯 Test: {test_text}"

        try:
            await bot.send_document(
                target_id,
                doc,
                caption=cap[:1024],
                reply_markup=channel_application_kb(uid, ui_lang),
            )
            if data.get("resume_doc_id"):
                await bot.send_document(
                    target_id,
                    document=data["resume_doc_id"],
                    caption=f"📄 Resume file: {data.get('resume_doc_name') or 'resume'}",
                )
            if data.get("test_doc_id"):
                await bot.send_document(
                    target_id,
                    document=data["test_doc_id"],
                    caption=f"🎯 Test file: {data.get('test_doc_name') or 'test'}",
                )
        except Exception:
            pass

    await bot.send_message(
        chat_id,
        msg(ui_lang, "review_sent"),
        reply_markup=_main_kb(ui_lang),
    )
    _cleanup_pdf(pdf_path)


def _cleanup_pdf(pdf_path: str | None) -> None:
    if pdf_path:
        try:
            os.unlink(pdf_path)
        except OSError:
            pass


# ── Язык ────────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("lang:"))
async def cb_pick_language(query: CallbackQuery, state: FSMContext) -> None:
    code = (query.data or "").split(":", 1)[1]
    if code not in ("ru", "uz") or not query.from_user:
        return
    await query.answer()
    await state.clear()
    await ensure_bot_user(
        query.from_user.id,
        query.from_user.username,
        query.from_user.first_name,
    )
    await set_user_locale(query.from_user.id, code)
    chat_id = query.message.chat.id if query.message else query.from_user.id
    try:
        if query.message:
            await query.message.delete()
    except TelegramBadRequest:
        pass
    await query.bot.send_message(chat_id, msg(code, "lang_saved"))
    await query.bot.send_message(chat_id, msg(code, "start"), reply_markup=main_menu_kb(code))


@router.message(Command("lang"))
async def cmd_lang(message: Message, state: FSMContext) -> None:
    await message.answer(pick_language_prompt(), reply_markup=language_pick_kb())


# ─────────────────────────── Review callbacks ───────────────────────

@router.callback_query(F.data == "rev:ok", ReviewState.waiting)
async def review_confirm(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    data = await state.get_data()
    pdf_path: str | None = data.get("pdf_path")
    vacancy_title: str = data.get("vacancy_title", "")
    applicant_label: str = data.get("applicant_label", "")
    uid: int = data.get("applicant_uid", query.from_user.id if query.from_user else 0)
    lg: str = data.get("review_ui_lang") or LANG_UZ
    await state.clear()

    target = conf.bot.target_chat_id
    if target and pdf_path and os.path.isfile(pdf_path):
        try:
            target_id: int | str = int(target)
        except ValueError:
            target_id = target
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        cap = msg(lg, "channel_new_apply", title=vacancy_title, label=applicant_label)
        doc = BufferedInputFile(pdf_bytes, filename="zayavka.pdf")
        try:
            await query.bot.send_document(
                target_id,
                doc,
                caption=cap[:1024],
                reply_markup=channel_application_kb(uid, lg),
            )
        except Exception:
            pass

    _cleanup_pdf(pdf_path)

    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    await query.message.answer(
        msg(lg, "review_sent"),
        reply_markup=_main_kb(lg),
    )


@router.callback_query(F.data == "rev:redo", ReviewState.waiting)
async def review_redo(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    data = await state.get_data()
    lg: str = data.get("review_ui_lang") or LANG_UZ
    _cleanup_pdf(data.get("pdf_path"))
    await state.clear()

    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    await query.message.answer(
        msg(lg, "review_redo"),
        reply_markup=_main_kb(lg),
    )


# ─────────────────────────── /start ─────────────────────────────────

@router.message(StateFilter("*"), CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not message.from_user:
        return
    await ensure_bot_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )
    await message.answer(pick_language_prompt(), reply_markup=language_pick_kb())


@router.message(F.text.in_(all_labels("btn_company")))
async def menu_company(message: Message) -> None:
    lang = await _require_language_or_hint(message)
    if lang is None:
        return
    await message.answer(msg(lang, "company_info"))


@router.message(F.text.in_(all_labels("btn_services")))
async def menu_services(message: Message) -> None:
    lang = await _require_language_or_hint(message)
    if lang is None:
        return
    await message.answer(msg(lang, "services_dev"))


# ─────────────────────────── Vacancy view (client) ──────────────────

@router.message(F.text.in_(all_labels("btn_view")))
async def menu_view_vacancies(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not message.from_user:
        return
    lang = await _require_language_or_hint(message)
    if lang is None:
        return
    r = await db.execute(
        select(Vacancy)
        .where(Vacancy.is_active.is_(True))
        .order_by(Vacancy.sort_order, Vacancy.id)
    )
    vacs = list(r.scalars().all())
    if not vacs:
        await message.answer(msg(lang, "view_empty"), reply_markup=_main_kb(lang))
        return
    await message.answer(
        msg(lang, "view_header"),
        reply_markup=vacancy_view_list_kb(vacs, lang),
    )


@router.callback_query(F.data.startswith("vview:"))
async def cb_vacancy_view(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    raw = query.data or ""
    uid = query.from_user.id if query.from_user else 0
    lang = await _user_lang(uid)

    if raw == "vview:back":
        try:
            await query.message.edit_text(msg(lang, "view_back_main"))
        except TelegramBadRequest:
            await query.message.answer(msg(lang, "view_back_main"))
        await query.message.answer(" ", reply_markup=_main_kb(lang))
        return

    try:
        vid = int(raw.split(":", 1)[1])
    except (ValueError, IndexError):
        return

    v = await Vacancy.get_or_none(vid)
    if not v or not v.is_active:
        await query.message.answer(msg(lang, "vac_na"))
        return

    desc = (_bilingual_value(v, lang, "description") or "").strip() or msg(lang, "vac_desc_none")
    title = (_bilingual_value(v, lang, "title") or v.title).strip()
    text = msg(
        lang,
        "vac_card",
        title=title,
        desc=desc,
    )
    try:
        await query.message.edit_text(text, reply_markup=vacancy_view_detail_kb(vid, lang))
    except TelegramBadRequest:
        await query.message.answer(text, reply_markup=vacancy_view_detail_kb(vid, lang))


async def _send_hr_result(query_or_message: Message | CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if isinstance(query_or_message, CallbackQuery):
        user = query_or_message.from_user
        bot = query_or_message.bot
        message = query_or_message.message
    else:
        user = query_or_message.from_user
        bot = query_or_message.bot
        message = query_or_message

    lang = data.get("ui_lang", LANG_UZ)
    if not user:
        await state.clear()
        return

    username = f"@{user.username}" if user.username else "без username"
    applicant_label = f"{data.get('full_name')} ({username}) id:{user.id}"
    custom_answers: list[dict] = data.get("custom_answers") or []

    rows: list[tuple[str, str]] = [
        ("Имя и фамилия", data.get("full_name") or "—"),
        ("Телефон", data.get("phone") or "—"),
        ("Город", data.get("city") or "—"),
        ("Резюме", data.get("resume_text") or f"Файл: {data.get('resume_doc_name') or '-'}"),
        ("Портфолио", data.get("portfolio") or "—"),
        ("Тестовое", data.get("test_text") or f"Файл: {data.get('test_doc_name') or '-'}"),
    ]
    for i, row in enumerate(custom_answers, 1):
        rows.append((f"Вопрос {i}", f"{row.get('q')}\nОтвет: {row.get('a') or '—'}"))

    pdf_path: str | None = None
    pdf_bytes: bytes | None = None
    try:
        pdf_path = build_candidate_compact_pdf(
            vacancy_title=f"Отклик: {data.get('vacancy_title', 'Сценарист')}",
            applicant_label=applicant_label,
            rows=rows,
        )
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    except Exception:
        pdf_path = None
        pdf_bytes = None

    target = conf.bot.target_chat_id
    if target:
        try:
            target_id: int | str = int(target)
        except ValueError:
            target_id = target

        summary = (
            f"⚡️ Новый отклик на вакансию: {data.get('vacancy_title', 'Сценарист')}\n"
            f"👤 Кандидат: {data.get('full_name')} ({username})\n"
            f"📞 Телефон: {data.get('phone')}\n"
            f"🏙 Город: {data.get('city')}\n"
            f"📄 Резюме: {data.get('resume_text') or 'прикреплено файлом'}\n"
            f"📁 Портфолио: {data.get('portfolio')}\n"
            f"🎯 Тестовое: {data.get('test_text') or 'прикреплено файлом'}\n"
            f"❓ Кастомных ответов: {len(custom_answers)}\n\n"
            f"{msg(lang, 'channel_interview_note')}\n"
            f"🔗 Telegram: tg://user?id={user.id}"
        )
        try:
            await bot.send_message(
                target_id,
                summary,
                reply_markup=channel_application_kb(user.id, lang),
            )
            if pdf_bytes:
                await bot.send_document(
                    target_id,
                    document=BufferedInputFile(pdf_bytes, filename="candidate_card.pdf"),
                    caption=f"📎 <b>PDF-карточка кандидата</b>\n👤 {applicant_label}\n💼 Вакансия: {data.get('vacancy_title', 'Сценарист')}",
                )
            if data.get("resume_doc_id"):
                await bot.send_document(
                    target_id,
                    document=data["resume_doc_id"],
                    caption=f"📄 Резюме: {data.get('resume_doc_name') or 'file'}",
                )
            if data.get("test_doc_id"):
                await bot.send_document(
                    target_id,
                    document=data["test_doc_id"],
                    caption=f"🎯 Тестовое: {data.get('test_doc_name') or 'file'}",
                )
        except Exception:
            pass

    if pdf_bytes:
        await message.answer_document(
            document=BufferedInputFile(pdf_bytes, filename="candidate_card.pdf"),
            caption=f"📎 <b>Ваша анкета (PDF)</b>\n👤 Кандидат: {applicant_label}\n💼 Вакансия: {data.get('vacancy_title', 'Сценарист')}",
        )

    if pdf_path:
        _cleanup_pdf(pdf_path)
    _cancel_reminder(user.id)
    await state.clear()
    await message.answer(msg(lang, "hr_done_user"), reply_markup=_main_kb(lang))


async def _ask_hr_custom_question(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("ui_lang", LANG_UZ)
    questions = data.get("custom_questions") or []
    idx = data.get("custom_idx", 0)
    if idx >= len(questions):
        await state.set_state(HRCandidateState.waiting_test_choice)
        await _send_hr_test_step(message, state)
        return

    q = questions[idx]
    text = f"❓ <b>{idx + 1} / {len(questions)}</b>\n\n{q['text']}"
    await message.answer(text + "\n\n" + msg(lang, "form_hint_text"), reply_markup=_stop_kb(lang))


async def _send_hr_test_step(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("ui_lang", LANG_UZ)
    vacancy = await Vacancy.get_or_none(data.get("vacancy_id"))
    task_text = ((_bilingual_value(vacancy, lang, "test_task_text") or "").strip()) if vacancy else ""
    if task_text:
        await message.answer(task_text, reply_markup=_stop_kb(lang))
        await message.answer(msg(lang, "hr_test_waiting"), reply_markup=hr_test_choice_kb(lang))
        return

    await state.update_data(test_text=None, test_doc_id=None, test_doc_name=None)
    await _send_hr_result(message, state)


@router.callback_query(F.data.startswith("hrapply:"))
async def cb_hr_apply(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    raw = query.data or ""
    lang = await _user_lang(query.from_user.id if query.from_user else 0)
    try:
        vid = int(raw.split(":", 1)[1])
    except (ValueError, IndexError):
        return
    v = await Vacancy.get_or_none(vid)
    if not v or not v.is_active:
        await query.message.answer(msg(lang, "vac_na"))
        return
    await state.clear()
    title = (_bilingual_value(v, lang, "title") or v.title).strip()
    await state.update_data(vacancy_id=vid, vacancy_title=title, ui_lang=lang)
    await query.message.answer(msg(lang, "hr_pd_text"), reply_markup=hr_pd_consent_kb(vid, lang))


@router.callback_query(F.data.startswith("hragree:"))
async def cb_hr_agree(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    raw = query.data or ""
    lang = await _user_lang(query.from_user.id if query.from_user else 0)
    try:
        vid = int(raw.split(":", 1)[1])
    except (ValueError, IndexError):
        return
    v = await Vacancy.get_or_none(vid)
    if not v or not v.is_active:
        await query.message.answer(msg(lang, "vac_na"))
        return
    title = (_bilingual_value(v, lang, "title") or v.title).strip()
    await state.set_state(HRCandidateState.waiting_name)
    await state.update_data(
        vacancy_id=vid,
        vacancy_title=title,
        ui_lang=lang,
        custom_questions=[],
        custom_answers=[],
        custom_idx=0,
    )
    await query.message.answer(msg(lang, "hr_name_q"), reply_markup=_stop_kb(lang))


@router.message(HRCandidateState.waiting_name, F.text)
async def hr_name_step(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    await state.update_data(full_name=message.text.strip())
    await state.set_state(HRCandidateState.waiting_phone)
    await message.answer(msg(lang, "hr_phone_q"), reply_markup=_phone_kb(lang))


@router.message(HRCandidateState.waiting_phone, F.contact)
async def hr_phone_contact(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(HRCandidateState.waiting_city)
    await message.answer(msg(lang, "hr_city_q"), reply_markup=hr_city_kb())


@router.message(HRCandidateState.waiting_phone, F.text)
async def hr_phone_text(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    txt = message.text.strip()
    if len(txt) < 6:
        await message.answer(msg(lang, "hr_invalid_phone"), reply_markup=_phone_kb(lang))
        return
    await state.update_data(phone=txt)
    await state.set_state(HRCandidateState.waiting_city)
    await message.answer(msg(lang, "hr_city_q"), reply_markup=hr_city_kb())


@router.callback_query(HRCandidateState.waiting_city, F.data.startswith("hrcity:"))
async def hr_city_step(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    city = (query.data or "").split(":", 1)[1]
    await state.update_data(city=city)
    await state.set_state(HRCandidateState.waiting_resume)
    await query.message.answer(msg(lang, "hr_resume_q"), reply_markup=_stop_kb(lang))


@router.message(HRCandidateState.waiting_resume, F.document)
async def hr_resume_doc(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    doc = message.document
    if not _allowed_doc_name(doc.file_name):
        await message.answer(msg(lang, "hr_invalid_resume"), reply_markup=_stop_kb(lang))
        return
    await state.update_data(resume_doc_id=doc.file_id, resume_doc_name=doc.file_name, resume_text=None)
    await state.set_state(HRCandidateState.waiting_portfolio)
    await message.answer(msg(lang, "hr_portfolio_q"), reply_markup=_stop_kb(lang))


@router.message(HRCandidateState.waiting_resume, F.text)
async def hr_resume_text(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    text = message.text.strip()
    if not _is_url(text):
        await message.answer(msg(lang, "hr_invalid_resume"), reply_markup=_stop_kb(lang))
        return
    await state.update_data(resume_text=text, resume_doc_id=None, resume_doc_name=None)
    await state.set_state(HRCandidateState.waiting_portfolio)
    await message.answer(msg(lang, "hr_portfolio_q"), reply_markup=_stop_kb(lang))


@router.message(HRCandidateState.waiting_portfolio, F.text)
async def hr_portfolio_step(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    text = message.text.strip()
    if not _is_url(text):
        await message.answer(msg(lang, "hr_invalid_portfolio"), reply_markup=_stop_kb(lang))
        return
    await state.update_data(portfolio=text)
    data = await state.get_data()
    qs = await _load_questions(data.get("vacancy_id"))
    if qs:
        custom_questions = [
            {
                "id": q.id,
                "text": ((_bilingual_value(q, lang, "text") or q.text).strip()),
                "require_photo": q.require_photo,
            }
            for q in qs
        ]
        await state.update_data(custom_questions=custom_questions, custom_answers=[], custom_idx=0)
        await state.set_state(HRCandidateState.waiting_custom_answer)
        await _ask_hr_custom_question(message, state)
        return
    await state.set_state(HRCandidateState.waiting_test_choice)
    await _send_hr_test_step(message, state)


@router.message(HRCandidateState.waiting_custom_answer, F.text)
async def hr_custom_answer_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("ui_lang", LANG_UZ)
    questions = data.get("custom_questions") or []
    idx = data.get("custom_idx", 0)
    if idx >= len(questions):
        await state.set_state(HRCandidateState.waiting_test_choice)
        await _send_hr_test_step(message, state)
        return
    q = questions[idx]
    answers = data.get("custom_answers") or []
    answers.append({"q": q["text"], "a": message.text.strip(), "photo": None})
    await state.update_data(custom_answers=answers, custom_idx=idx + 1)
    await _ask_hr_custom_question(message, state)


@router.message(HRCandidateState.waiting_custom_answer, F.photo)
async def hr_custom_answer_photo(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    await message.answer(msg(lang, "answer_text_only"), reply_markup=_stop_kb(lang))


@router.callback_query(HRCandidateState.waiting_test_choice, F.data == "hrtest:later")
async def hr_test_later(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    data = await state.get_data()
    lang = data.get("ui_lang", LANG_UZ)
    if query.from_user:
        await _schedule_reminder(query.from_user.id, query.message.chat.id, query.bot, lang)
    await query.message.answer(msg(lang, "hr_test_later_ok"), reply_markup=_main_kb(lang))
    await state.clear()


@router.callback_query(HRCandidateState.waiting_test_choice, F.data == "hrtest:send")
async def hr_test_send(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    await state.set_state(HRCandidateState.waiting_test_submit)
    await query.message.answer(msg(lang, "hr_test_waiting"), reply_markup=_stop_kb(lang))


@router.message(HRCandidateState.waiting_test_submit, F.document)
async def hr_test_submit_doc(message: Message, state: FSMContext) -> None:
    doc = message.document
    if not _allowed_doc_name(doc.file_name):
        lang = (await state.get_data()).get("ui_lang", LANG_UZ)
        await message.answer(msg(lang, "hr_invalid_test"))
        return
    await state.update_data(test_doc_id=doc.file_id, test_doc_name=doc.file_name, test_text=None)
    await _send_hr_result(message, state)


@router.message(HRCandidateState.waiting_test_submit, F.text)
async def hr_test_submit_text(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text:
        lang = (await state.get_data()).get("ui_lang", LANG_UZ)
        await message.answer(msg(lang, "hr_invalid_text"))
        return
    await state.update_data(test_text=text, test_doc_id=None, test_doc_name=None)
    await _send_hr_result(message, state)


@router.message(
    HRCandidateState.waiting_name,
    HRCandidateState.waiting_portfolio,
    HRCandidateState.waiting_custom_answer,
    HRCandidateState.waiting_test_submit,
)
async def hr_text_only_fallback(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    await message.answer(msg(lang, "hr_invalid_text"))


@router.message(HRCandidateState.waiting_resume)
async def hr_resume_invalid(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    await message.answer(msg(lang, "hr_invalid_resume"))


@router.message(HRCandidateState.waiting_city)
async def hr_city_invalid(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    await message.answer(msg(lang, "hr_city_q"), reply_markup=hr_city_kb())


# ─────────────────────────── Apply ──────────────────────────────────

@router.message(F.text.in_(all_labels("btn_apply")))
async def menu_apply(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not message.from_user:
        return
    lang = await _require_language_or_hint(message)
    if lang is None:
        return
    await ensure_bot_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )
    r = await db.execute(
        select(Vacancy)
        .where(Vacancy.is_active.is_(True))
        .order_by(Vacancy.sort_order, Vacancy.id)
    )
    vacs = list(r.scalars().all())
    if not vacs:
        await message.answer(msg(lang, "apply_empty"), reply_markup=_main_kb(lang))
        return
    await message.answer(msg(lang, "apply_pick"), reply_markup=vacancies_kb(vacs, lang))


@router.callback_query(F.data.startswith("vac:"))
async def cb_vacancy_pick(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    raw = query.data or ""
    uid = query.from_user.id if query.from_user else 0
    lang = await _user_lang(uid)

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
        await query.message.answer(msg(lang, "vac_na"))
        return

    qs = await _load_questions(vid)
    if not qs:
        await query.message.answer(msg(lang, "vac_no_questions"))
        return

    questions = [
        {
            "id": q.id,
            "text": ((_bilingual_value(q, lang, "text") or q.text).strip()),
            "require_photo": q.require_photo,
        }
        for q in qs
    ]
    title = (_bilingual_value(v, lang, "title") or v.title).strip()
    await state.set_state(UserForm.answering)
    await state.update_data(
        vacancy_id=vid,
        vacancy_title=title,
        questions=questions,
        idx=0,
        answers=[],
        ui_lang=lang,
    )
    start_txt = msg(lang, "form_start", title=title)
    try:
        await query.message.edit_text(start_txt)
    except TelegramBadRequest:
        await query.message.answer(start_txt)
    await _ask_current(query, state)


# ─────────────────────────── Answering form ─────────────────────────

@router.message(UserForm.answering, F.text)
async def answer_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("ui_lang") or LANG_UZ
    questions = data.get("questions") or []
    idx = data.get("idx", 0)
    if idx >= len(questions):
        await state.clear()
        return
    q = questions[idx]
    stops = all_labels("btn_stop_form")
    if message.text in stops:
        await state.clear()
        await message.answer(msg(lang, "answer_stop"), reply_markup=_main_kb(lang))
        return
    answers = data.get("answers") or []
    answers.append({"question_id": q["id"], "text": message.text.strip(), "photo_path": None})
    await state.update_data(idx=idx + 1, answers=answers)
    await _ask_current(message, state)


@router.message(UserForm.answering, F.photo)
async def answer_photo(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang") or LANG_UZ
    await message.answer(msg(lang, "answer_text_only"), reply_markup=_stop_kb(lang))


@router.message(UserForm.answering)
async def answer_invalid(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("ui_lang") or LANG_UZ
    questions = data.get("questions") or []
    idx = data.get("idx", 0)
    if idx >= len(questions):
        return
    q = questions[idx]
    await message.answer(msg(lang, "answer_text_only"))


@router.message(PostFormState.waiting_resume, F.document)
async def post_resume_doc(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("ui_lang") or LANG_UZ
    doc = message.document
    if not _allowed_doc_name(doc.file_name):
        await message.answer(msg(lang, "hr_invalid_resume"), reply_markup=_stop_kb(lang))
        return

    await state.update_data(
        resume_doc_id=doc.file_id,
        resume_doc_name=doc.file_name,
        resume_text=None,
    )
    vacancy = await Vacancy.get_or_none(data.get("vacancy_id"))
    task_text = ((_bilingual_value(vacancy, lang, "test_task_text") or "").strip()) if vacancy else ""
    await state.set_state(PostFormState.waiting_test_submit)
    if task_text:
        await message.answer(task_text, reply_markup=_stop_kb(lang))
    else:
        await message.answer(msg(lang, "hr_test_waiting"), reply_markup=_stop_kb(lang))


@router.message(PostFormState.waiting_resume, F.text)
async def post_resume_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("ui_lang") or LANG_UZ
    text = message.text.strip()
    if not _is_url(text):
        await message.answer(msg(lang, "hr_invalid_resume"), reply_markup=_stop_kb(lang))
        return

    await state.update_data(resume_text=text, resume_doc_id=None, resume_doc_name=None)
    vacancy = await Vacancy.get_or_none(data.get("vacancy_id"))
    task_text = ((_bilingual_value(vacancy, lang, "test_task_text") or "").strip()) if vacancy else ""
    await state.set_state(PostFormState.waiting_test_submit)
    if task_text:
        await message.answer(task_text, reply_markup=_stop_kb(lang))
    else:
        await message.answer(msg(lang, "hr_test_waiting"), reply_markup=_stop_kb(lang))


@router.message(PostFormState.waiting_test_submit, F.document)
async def post_test_doc(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("ui_lang") or LANG_UZ
    doc = message.document
    if not _allowed_doc_name(doc.file_name):
        await message.answer(msg(lang, "hr_invalid_test"), reply_markup=_stop_kb(lang))
        return
    await state.update_data(test_doc_id=doc.file_id, test_doc_name=doc.file_name, test_text=None)
    await _finalize_to_channel(message.bot, state, message.chat.id, message.from_user)


@router.message(PostFormState.waiting_test_submit, F.text)
async def post_test_text(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text:
        data = await state.get_data()
        lang = data.get("ui_lang") or LANG_UZ
        await message.answer(msg(lang, "hr_invalid_text"), reply_markup=_stop_kb(lang))
        return
    await state.update_data(test_text=text, test_doc_id=None, test_doc_name=None)
    await _finalize_to_channel(message.bot, state, message.chat.id, message.from_user)


@router.message(
    StateFilter(
        UserForm.answering,
        PostFormState.waiting_resume,
        PostFormState.waiting_test_submit,
        ReviewState.waiting,
        HRCandidateState.waiting_name,
        HRCandidateState.waiting_phone,
        HRCandidateState.waiting_city,
        HRCandidateState.waiting_resume,
        HRCandidateState.waiting_portfolio,
        HRCandidateState.waiting_custom_answer,
        HRCandidateState.waiting_test_choice,
        HRCandidateState.waiting_test_submit,
    ),
    F.text.in_(all_labels("btn_stop_form")),
)
@router.message(
    StateFilter(
        UserForm.answering,
        PostFormState.waiting_resume,
        PostFormState.waiting_test_submit,
        ReviewState.waiting,
        HRCandidateState.waiting_name,
        HRCandidateState.waiting_phone,
        HRCandidateState.waiting_city,
        HRCandidateState.waiting_resume,
        HRCandidateState.waiting_portfolio,
        HRCandidateState.waiting_custom_answer,
        HRCandidateState.waiting_test_choice,
        HRCandidateState.waiting_test_submit,
    ),
    Command("cancel"),
)
async def stop_any_fsm(message: Message, state: FSMContext) -> None:
    if message.from_user:
        _cancel_reminder(message.from_user.id)
    lang = (await state.get_data()).get("ui_lang") or (await _user_lang(message.from_user.id if message.from_user else 0))
    await state.clear()
    await message.answer(msg(lang, "answer_stop"), reply_markup=_main_kb(lang))
