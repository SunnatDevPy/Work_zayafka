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
    Message,
    ReplyKeyboardMarkup,
)
from sqlalchemy import select

from config import conf
from keyboards.inline import (
    channel_application_kb,
    city_answer_for_pdf,
    hr_city_kb,
    hr_employment_kb,
    hr_payment_kb,
    hr_pd_consent_kb,
    hr_review_kb,
    language_pick_kb,
    vacancies_kb,
    vacancy_view_detail_kb,
    vacancy_view_list_kb,
)
from locales.messages import LANG_UZ, all_labels, main_menu_kb, msg, norm_lang, pick_language_prompt
from models.database import db
from models.vacancy import Vacancy
from services.pdf import build_candidate_compact_pdf
from survey_definitions import SURVEY_ITEMS, survey_ask_html, survey_pdf_label
from utils.user_locale import ensure_bot_user, get_user_locale, set_user_locale

router = Router(name="user")


class HRCandidateState(StatesGroup):
    waiting_photo = State()
    waiting_survey = State()


class HRCandidateReviewState(StatesGroup):
    waiting = State()


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


def _main_kb(lang: str) -> ReplyKeyboardMarkup:
    return main_menu_kb(lang)


async def _user_lang(telegram_id: int) -> str:
    loc = await get_user_locale(telegram_id)
    return norm_lang(loc) if loc else LANG_UZ


async def _require_language_or_hint(message: Message) -> str | None:
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
        return ru or uz or getattr(obj, base, None)
    return uz or ru or getattr(obj, base, None)


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
            payload = payload[len(prefix) :]
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


async def _send_survey_question(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    step: int = data.get("survey_step") or 1
    lang = data.get("ui_lang", LANG_UZ)
    if step < 1 or step > len(SURVEY_ITEMS):
        return
    item = SURVEY_ITEMS[step - 1]
    text = survey_ask_html(item, lang)
    if item["kind"] == "phone":
        await message.answer(text, reply_markup=_phone_kb(lang))
    elif item["kind"] == "city":
        await message.answer(text, reply_markup=hr_city_kb(lang))
    elif item["kind"] == "employment":
        await message.answer(text, reply_markup=hr_employment_kb(lang))
    elif item["kind"] == "payment":
        await message.answer(text, reply_markup=hr_payment_kb(lang))
    else:
        await message.answer(text, reply_markup=_stop_kb(lang))


async def _advance_survey(message: Message, state: FSMContext, answer: str) -> None:
    data = await state.get_data()
    step: int = data.get("survey_step") or 1
    lang = data.get("ui_lang", LANG_UZ)
    answers = list(data.get("survey_answers") or [])
    if len(answers) != step - 1:
        answers = answers[: max(0, step - 1)]
    answers.append(answer)
    await state.update_data(survey_answers=answers)
    if step >= len(SURVEY_ITEMS):
        await _prepare_hr_review(message, state)
        return
    await state.update_data(survey_step=step + 1)
    await _send_survey_question(message, state)


async def _prepare_hr_review(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    user = message.from_user
    bot = message.bot
    lang = data.get("ui_lang", LANG_UZ)
    if not user:
        await state.clear()
        return

    answers: list[str] = list(data.get("survey_answers") or [])
    full_name = answers[0] if answers else None
    username = f"@{user.username}" if user.username else "—"
    applicant_label = f"{full_name or '—'} ({username}) id:{user.id}"

    rows: list[tuple[str, str]] = []
    for i, item in enumerate(SURVEY_ITEMS):
        label = survey_pdf_label(item, lang)
        val = answers[i] if i < len(answers) else "—"
        rows.append((label, val))

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
            vacancy_title=f"{msg(lang, 'pdf_reply_title')}: {data.get('vacancy_title', '—')}",
            applicant_label=applicant_label,
            rows=rows,
            photo_path=user_photo_path,
            photo_caption=msg(lang, "pdf_photo_caption"),
            col_field=msg(lang, "pdf_col_field"),
            col_value=msg(lang, "pdf_col_value"),
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

    await state.update_data(hr_review_pdf_path=pdf_path, full_name=full_name)
    await state.set_state(HRCandidateReviewState.waiting)
    await message.answer_document(
        document=BufferedInputFile(pdf_bytes, filename=_hr_candidate_pdf_filename(full_name)),
        caption=msg(lang, "review_caption"),
        reply_markup=hr_review_kb(lang),
    )


_HR_STOP_STATES = (
    HRCandidateReviewState.waiting,
    HRCandidateState.waiting_photo,
    HRCandidateState.waiting_survey,
)


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
    vac_title = data.get("vacancy_title", "—")
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
    text = msg(lang, "vac_card", title=title, desc=desc)
    try:
        await query.message.edit_text(text, reply_markup=vacancy_view_detail_kb(vid, lang))
    except TelegramBadRequest:
        await query.message.answer(text, reply_markup=vacancy_view_detail_kb(vid, lang))


@router.message(
    StateFilter(*_HR_STOP_STATES),
    F.text.in_(all_labels("btn_stop_form")),
)
@router.message(
    StateFilter(*_HR_STOP_STATES),
    Command("cancel"),
)
async def stop_any_fsm(message: Message, state: FSMContext) -> None:
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
    await state.set_state(HRCandidateState.waiting_photo)
    await state.update_data(
        vacancy_id=vid,
        vacancy_title=title,
        ui_lang=lang,
        survey_step=1,
        survey_answers=[],
        candidate_photo_id=None,
        hr_review_pdf_path=None,
        full_name=None,
    )
    try:
        await query.message.delete()
    except TelegramBadRequest:
        pass
    await query.message.answer(msg(lang, "hr_photo_first_q"), reply_markup=_stop_kb(lang))


@router.message(HRCandidateState.waiting_photo, F.photo)
async def hr_photo_first(message: Message, state: FSMContext) -> None:
    await state.update_data(candidate_photo_id=message.photo[-1].file_id)
    await state.set_state(HRCandidateState.waiting_survey)
    await _send_survey_question(message, state)


@router.message(HRCandidateState.waiting_photo)
async def hr_photo_invalid(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    await message.answer(msg(lang, "hr_invalid_photo"), reply_markup=_stop_kb(lang))


@router.message(HRCandidateState.waiting_survey, F.contact)
async def survey_phone_contact(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    step: int = data.get("survey_step") or 1
    if step != 2 or SURVEY_ITEMS[1]["kind"] != "phone":
        return
    phone = message.contact.phone_number if message.contact else ""
    if not phone:
        lang = data.get("ui_lang", LANG_UZ)
        await message.answer(msg(lang, "hr_invalid_phone"), reply_markup=_phone_kb(lang))
        return
    await _advance_survey(message, state, phone)


@router.message(HRCandidateState.waiting_survey, F.text)
async def survey_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    step: int = data.get("survey_step") or 1
    lang = data.get("ui_lang", LANG_UZ)
    item = SURVEY_ITEMS[step - 1]
    txt = (message.text or "").strip()

    if item["kind"] == "phone":
        if len(txt) < 6:
            await message.answer(msg(lang, "hr_invalid_phone"), reply_markup=_phone_kb(lang))
            return
        await _advance_survey(message, state, txt)
        return

    if item["kind"] != "text":
        await message.answer(msg(lang, "hr_use_inline_hint"), reply_markup=_stop_kb(lang))
        return

    if len(txt) < 1:
        await message.answer(msg(lang, "hr_invalid_text"), reply_markup=_stop_kb(lang))
        return
    await _advance_survey(message, state, txt)


@router.callback_query(HRCandidateState.waiting_survey, F.data.startswith("hrcity:"))
async def survey_city(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    data = await state.get_data()
    if (data.get("survey_step") or 0) != 3:
        return

    raw = (query.data or "").split(":", 1)[1]
    lang = data.get("ui_lang", LANG_UZ)
    display = city_answer_for_pdf(raw, lang)
    await _advance_survey(query.message, state, display)
    try:
        await query.message.delete()
    except TelegramBadRequest:
        pass


@router.callback_query(HRCandidateState.waiting_survey, F.data.startswith("hremp:"))
async def survey_employment(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    data = await state.get_data()
    if (data.get("survey_step") or 0) != 4:
        return
    lang = data.get("ui_lang", LANG_UZ)
    value = (query.data or "").split(":", 1)[1]
    if value == "full":
        label = msg(lang, "hr_emp_full")
    elif value == "part":
        label = msg(lang, "hr_emp_part")
    elif value == "project":
        label = msg(lang, "hr_emp_project")
    else:
        return
    await _advance_survey(query.message, state, label)


@router.callback_query(HRCandidateState.waiting_survey, F.data.startswith("hrpay:"))
async def survey_payment(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    data = await state.get_data()
    if (data.get("survey_step") or 0) != 5:
        return
    lang = data.get("ui_lang", LANG_UZ)
    value = (query.data or "").split(":", 1)[1]
    if value == "fixed":
        label = msg(lang, "hr_pay_fixed")
    elif value == "scenario":
        label = msg(lang, "hr_pay_scenario")
    else:
        return
    await _advance_survey(query.message, state, label)


@router.message(HRCandidateState.waiting_survey)
async def survey_wrong_type(message: Message, state: FSMContext) -> None:
    lang = (await state.get_data()).get("ui_lang", LANG_UZ)
    await message.answer(msg(lang, "hr_invalid_text"), reply_markup=_stop_kb(lang))


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
