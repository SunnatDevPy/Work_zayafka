import asyncio
import os
import tempfile

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
    hr_employment_kb,
    hr_payment_kb,
    hr_pd_consent_kb,
    hr_review_kb,
    hr_test_choice_kb,
    language_pick_kb,
    vacancies_kb,
    vacancy_view_detail_kb,
    vacancy_view_list_kb,
)
from locales.messages import LANG_UZ, all_labels, main_menu_kb, msg, norm_lang, pick_language_prompt
from models.database import db
from models.vacancy import Vacancy
from services.pdf import build_candidate_compact_pdf
from utils.user_locale import ensure_bot_user, get_user_locale, set_user_locale

router = Router(name="user")


class HRCandidateState(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_city = State()
    waiting_employment = State()
    waiting_payment = State()
    waiting_income = State()
    waiting_resume = State()
    waiting_portfolio = State()
    waiting_photo = State()
    waiting_test_choice = State()
    waiting_test_submit = State()


class HRCandidateReviewState(StatesGroup):
    waiting = State()


_reminder_tasks: dict[int, asyncio.Task] = {}


async def _delete_prompt_message(bot, chat_id: int, state: FSMContext) -> None:
    data = await state.get_data()
    mid = data.get("bot_prompt_msg_id")
    if not mid:
        return
    try:
        await bot.delete_message(chat_id, mid)
    except Exception:
        pass
    await state.update_data(bot_prompt_msg_id=None)


async def _send_prompt(bot, chat_id: int, state: FSMContext, text: str, reply_markup=None):
    await _delete_prompt_message(bot, chat_id, state)
    sent = await bot.send_message(chat_id, text, reply_markup=reply_markup)
    await state.update_data(bot_prompt_msg_id=sent.message_id)
    return sent


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


def _hr_candidate_pdf_filename(full_name: str | None) -> str:
    base = (full_name or "").strip() or "candidate"
    cleaned: list[str] = []
    for ch in base[:100]:
        if ch in '<>:"/\\|?*\x00\n\r\t':
            cleaned.append("_")
        else:
            cleaned.append(ch)
    stem = "".join(cleaned).strip("._ ") or "candidate"
    return f"{stem}.pdf"


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
                f"⏰ {msg(lang, 'hr_test_reminder')}",
                reply_markup=hr_test_choice_kb(lang),
            )
        except asyncio.CancelledError:
            return
        finally:
            _reminder_tasks.pop(user_id, None)

    _reminder_tasks[user_id] = asyncio.create_task(_job())


def _main_kb(lang: str) -> ReplyKeyboardMarkup:
    """Главное меню по языку (используется после форм и сценария)."""
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


def _bilingual_value(obj, lang: str, base: str) -> str | None:
    ru = getattr(obj, f"{base}_ru", None)
    uz = getattr(obj, f"{base}_uz", None)
    if norm_lang(lang) == "ru":
        return (ru or uz or getattr(obj, base, None))
    return (uz or ru or getattr(obj, base, None))


async def _show_vacancy_card(message: Message, vacancy_id: int, lang: str) -> None:
    v = await Vacancy.get_or_none(vacancy_id)
    if not v or not v.is_active:
        await message.answer(msg(lang, "vac_na"), reply_markup=_main_kb(lang))
        return
    desc = (_bilingual_value(v, lang, "description") or "").strip() or msg(lang, "vac_desc_none")
    title = (_bilingual_value(v, lang, "title") or v.title).strip()
    await message.answer(
        msg(lang, "vac_card", title=title, desc=desc),
        reply_markup=vacancy_view_detail_kb(vacancy_id, lang),
    )


def _parse_start_vacancy_id(raw_text: str | None) -> int | None:
    if not raw_text:
        return None
    parts = raw_text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return None
    payload = parts[1].strip().lower()
    for prefix in ("vac_", "vacancy_", "vac:", "vview:"):
        if payload.startswith(prefix):
            payload = payload[len(prefix):]
            break
    try:
        return int(payload)
    except ValueError:
        return None


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
    data = await state.get_data()
    start_vacancy_id = data.get("start_vacancy_id")
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
    if start_vacancy_id and query.message:
        await _show_vacancy_card(query.message, int(start_vacancy_id), code)
        return
    await query.bot.send_message(chat_id, msg(code, "start"), reply_markup=main_menu_kb(code))


@router.message(Command("lang"))
async def cmd_lang(message: Message, state: FSMContext) -> None:
    await message.answer(pick_language_prompt(), reply_markup=language_pick_kb())


# ─────────────────────────── HR review callbacks ────────────────────

@router.callback_query(F.data == "hrrev:ok", HRCandidateReviewState.waiting)
async def hr_review_confirm(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    data = await state.get_data()
    pdf_path: str | None = data.get("hr_review_pdf_path")
    lang = data.get("ui_lang", LANG_UZ)
    user = query.from_user
    if not user:
        await state.clear()
        return

    username = f"@{user.username}" if user.username else "без username"
    vac_title = data.get("vacancy_title", "Сценарист")
    full_name = data.get("full_name") or "—"
    cap = (
        f"⚡️ <b>{vac_title}</b>\n"
        f"👤 {full_name} · {username}\n"
        f"🆔 <code>{user.id}</code>"
    )
    if len(cap) > 1024:
        cap = cap[:1021] + "..."

    target = conf.bot.target_chat_id
    if target and pdf_path and os.path.isfile(pdf_path):
        try:
            target_id: int | str = int(target)
        except ValueError:
            target_id = target
        try:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            await query.bot.send_document(
                target_id,
                document=BufferedInputFile(
                    pdf_bytes, filename=_hr_candidate_pdf_filename(data.get("full_name"))
                ),
                caption=cap,
                reply_markup=channel_application_kb(user.id, lang),
            )
        except Exception:
            pass

    _cleanup_pdf(pdf_path)
    _cancel_reminder(user.id)
    await state.clear()

    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    await query.message.answer(msg(lang, "hr_done_user"), reply_markup=_main_kb(lang))


@router.callback_query(F.data == "hrrev:redo", HRCandidateReviewState.waiting)
async def hr_review_redo(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    data = await state.get_data()
    lang = data.get("ui_lang", LANG_UZ)
    _cleanup_pdf(data.get("hr_review_pdf_path"))
    _cancel_reminder(query.from_user.id if query.from_user else 0)
    await state.clear()

    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    await query.message.answer(msg(lang, "review_redo"), reply_markup=_main_kb(lang))


@router.message(HRCandidateReviewState.waiting)
async def hr_review_wrong_input(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    await message.answer(msg(lang, "hr_review_hint"))


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
    start_vacancy_id = _parse_start_vacancy_id(message.text)
    if start_vacancy_id:
        await state.update_data(start_vacancy_id=start_vacancy_id)
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


async def _prepare_hr_review(message: Message, state: FSMContext) -> None:
    """Собрать PDF и показать пользователю подтверждение (отправить / заново) перед каналом."""
    data = await state.get_data()
    user = message.from_user
    bot = message.bot
    lang = data.get("ui_lang", LANG_UZ)
    if not user:
        await state.clear()
        return

    username = f"@{user.username}" if user.username else "без username"
    applicant_label = f"{data.get('full_name')} ({username}) id:{user.id}"

    rows: list[tuple[str, str]] = [
        ("Имя и фамилия", data.get("full_name") or "—"),
        ("Телефон", data.get("phone") or "—"),
        ("Город", data.get("city") or "—"),
        ("Занятость", data.get("employment") or "—"),
        ("Формат оплаты", data.get("payment") or "—"),
        ("Ожидания по доходу", data.get("income_expectation") or "—"),
        ("Резюме", data.get("resume_text") or f"Файл: {data.get('resume_doc_name') or '-'}"),
        ("Портфолио", data.get("portfolio") or "—"),
        ("Тестовое", data.get("test_text") or f"Файл: {data.get('test_doc_name') or '-'}"),
    ]

    user_photo_path: str | None = None
    if data.get("candidate_photo_id"):
        try:
            fd, user_photo_path = tempfile.mkstemp(suffix=".jpg")
            os.close(fd)
            await bot.download(data["candidate_photo_id"], destination=user_photo_path)
        except Exception:
            _cleanup_pdf(user_photo_path)
            user_photo_path = None

    pdf_path: str | None = None
    pdf_bytes: bytes | None = None
    try:
        pdf_path = build_candidate_compact_pdf(
            vacancy_title=f"Отклик: {data.get('vacancy_title', 'Сценарист')}",
            applicant_label=applicant_label,
            rows=rows,
            photo_path=user_photo_path,
        )
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    except Exception:
        pdf_path = None
        pdf_bytes = None
    finally:
        if user_photo_path:
            _cleanup_pdf(user_photo_path)

    if not pdf_bytes or not pdf_path:
        await message.answer(msg(lang, "hr_pdf_error"), reply_markup=_stop_kb(lang))
        return

    await state.update_data(hr_review_pdf_path=pdf_path)
    await state.set_state(HRCandidateReviewState.waiting)
    await message.answer_document(
        document=BufferedInputFile(
            pdf_bytes, filename=_hr_candidate_pdf_filename(data.get("full_name"))
        ),
        caption=msg(lang, "review_caption"),
        reply_markup=hr_review_kb(lang),
    )


async def _continue_hr_after_test(message: Message, state: FSMContext) -> None:
    """После тестового — сразу предпросмотр PDF (без доп. вопросов из БД)."""
    await _prepare_hr_review(message, state)


async def _send_hr_test_step(message: Message, state: FSMContext) -> None:
    """После фото: одно сообщение с заданием «сценарий» и кнопки; PDF после отправки ответа."""
    data = await state.get_data()
    lang = data.get("ui_lang", LANG_UZ)
    chat_id = message.chat.id
    bot = message.bot
    await state.update_data(test_text=None, test_doc_id=None, test_doc_name=None)
    await _send_prompt(
        bot,
        chat_id,
        state,
        msg(lang, "scenario_task_prompt"),
        reply_markup=hr_test_choice_kb(lang),
    )


_HR_STOP_STATES = (
    HRCandidateReviewState.waiting,
    HRCandidateState.waiting_name,
    HRCandidateState.waiting_phone,
    HRCandidateState.waiting_city,
    HRCandidateState.waiting_employment,
    HRCandidateState.waiting_payment,
    HRCandidateState.waiting_income,
    HRCandidateState.waiting_resume,
    HRCandidateState.waiting_portfolio,
    HRCandidateState.waiting_photo,
    HRCandidateState.waiting_test_choice,
    HRCandidateState.waiting_test_submit,
)


@router.message(
    StateFilter(*_HR_STOP_STATES),
    F.text.in_(all_labels("btn_stop_form")),
)
@router.message(
    StateFilter(*_HR_STOP_STATES),
    Command("cancel"),
)
async def stop_any_fsm(message: Message, state: FSMContext) -> None:
    if message.from_user:
        _cancel_reminder(message.from_user.id)
    await _delete_prompt_message(message.bot, message.chat.id, state)
    data = await state.get_data()
    _cleanup_pdf(data.get("hr_review_pdf_path"))
    lang = data.get("ui_lang") or (await _user_lang(message.from_user.id if message.from_user else 0))
    await state.clear()
    await message.answer(msg(lang, "answer_stop"), reply_markup=_main_kb(lang))


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
    try:
        await query.message.delete()
    except TelegramBadRequest:
        pass
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
    )
    try:
        await query.message.delete()
    except TelegramBadRequest:
        pass
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
    try:
        await query.message.delete()
    except TelegramBadRequest:
        pass
    await state.set_state(HRCandidateState.waiting_employment)
    await query.message.answer(msg(lang, "hr_emp_q"), reply_markup=hr_employment_kb(lang))


@router.callback_query(HRCandidateState.waiting_employment, F.data.startswith("hremp:"))
async def hr_employment_step(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    value = (query.data or "").split(":", 1)[1]
    employment = msg(lang, "hr_emp_full") if value == "full" else msg(lang, "hr_emp_part")
    await state.update_data(employment=employment)
    await state.set_state(HRCandidateState.waiting_payment)
    await query.message.answer(msg(lang, "hr_pay_q"), reply_markup=hr_payment_kb(lang))


@router.callback_query(HRCandidateState.waiting_payment, F.data.startswith("hrpay:"))
async def hr_payment_step(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    value = (query.data or "").split(":", 1)[1]
    payment = msg(lang, "hr_pay_salary") if value == "salary" else msg(lang, "hr_pay_piece")
    await state.update_data(payment=payment)
    await state.set_state(HRCandidateState.waiting_income)
    await query.message.answer(msg(lang, "hr_income_q"), reply_markup=_stop_kb(lang))


@router.message(HRCandidateState.waiting_income, F.text)
async def hr_income_step(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    income = message.text.strip()
    if len(income) < 2:
        await message.answer(msg(lang, "hr_invalid_text"), reply_markup=_stop_kb(lang))
        return
    await state.update_data(income_expectation=income)
    await state.set_state(HRCandidateState.waiting_resume)
    await message.answer(msg(lang, "hr_resume_q"), reply_markup=_stop_kb(lang))


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
    await state.set_state(HRCandidateState.waiting_photo)
    await message.answer(msg(lang, "hr_photo_q"), reply_markup=_stop_kb(lang))


@router.message(HRCandidateState.waiting_photo, F.photo)
async def hr_photo_step(message: Message, state: FSMContext) -> None:
    await state.update_data(candidate_photo_id=message.photo[-1].file_id)
    await state.set_state(HRCandidateState.waiting_test_choice)
    await _send_hr_test_step(message, state)


@router.message(HRCandidateState.waiting_photo)
async def hr_photo_invalid(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    await message.answer(msg(lang, "hr_invalid_photo"), reply_markup=_stop_kb(lang))


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
    await state.set_state(HRCandidateState.waiting_test_submit)
    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass


@router.message(HRCandidateState.waiting_test_submit, F.document)
async def hr_test_submit_doc(message: Message, state: FSMContext) -> None:
    doc = message.document
    if not _allowed_doc_name(doc.file_name):
        lang = (await state.get_data()).get("ui_lang", LANG_UZ)
        await message.answer(msg(lang, "hr_invalid_test"))
        return
    await state.update_data(test_doc_id=doc.file_id, test_doc_name=doc.file_name, test_text=None)
    await _continue_hr_after_test(message, state)


@router.message(HRCandidateState.waiting_test_submit, F.text)
async def hr_test_submit_text(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text:
        lang = (await state.get_data()).get("ui_lang", LANG_UZ)
        await message.answer(msg(lang, "hr_invalid_text"))
        return
    await state.update_data(test_text=text, test_doc_id=None, test_doc_name=None)
    await _continue_hr_after_test(message, state)


@router.message(
    HRCandidateState.waiting_name,
    HRCandidateState.waiting_employment,
    HRCandidateState.waiting_payment,
    HRCandidateState.waiting_income,
    HRCandidateState.waiting_portfolio,
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

    title = (_bilingual_value(v, lang, "title") or v.title).strip()
    await state.clear()
    await state.update_data(vacancy_id=vid, vacancy_title=title, ui_lang=lang)
    try:
        await query.message.delete()
    except TelegramBadRequest:
        pass
    await query.message.answer(msg(lang, "hr_pd_text"), reply_markup=hr_pd_consent_kb(vid, lang))
