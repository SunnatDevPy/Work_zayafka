"""User-facing FAQ handler."""

from html import escape

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from keyboards.inline import faq_detail_kb, faq_list_kb, language_pick_kb
from locales.messages import LANG_UZ, all_labels, msg, norm_lang, pick_language_prompt
from models.database import db
from models.faq import Faq
from utils.user_locale import get_user_locale

router = Router(name="faq")


async def _active_faqs() -> list[Faq]:
    r = await db.execute(select(Faq).order_by(Faq.sort_order, Faq.id))
    return list(r.scalars().all())


async def _faq_lang(telegram_id: int) -> str:
    loc = await get_user_locale(telegram_id)
    return norm_lang(loc) if loc else LANG_UZ


def _faq_q(f: Faq, lang: str) -> str:
    if norm_lang(lang) == "ru":
        return (f.question_ru or f.question_uz or f.question or "").strip()
    return (f.question_uz or f.question_ru or f.question or "").strip()


def _faq_a(f: Faq, lang: str) -> str:
    if norm_lang(lang) == "ru":
        return (f.answer_ru or f.answer_uz or f.answer or "").strip()
    return (f.answer_uz or f.answer_ru or f.answer or "").strip()


# ─────────────────────────── Entry point ────────────────────────────

@router.message(F.text.in_(all_labels("btn_faq")))
async def show_faq_list(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    if not await get_user_locale(message.from_user.id):
        await message.answer(pick_language_prompt(), reply_markup=language_pick_kb())
        return
    lang = await _faq_lang(message.from_user.id)
    faqs = await _active_faqs()
    if not faqs:
        await message.answer(msg(lang, "faq_empty"))
        return
    await message.answer(
        msg(lang, "faq_list_title"),
        reply_markup=faq_list_kb(faqs, lang),
    )


# ─────────────────────────── Inline callbacks ───────────────────────

@router.callback_query(F.data.startswith("faq:"))
async def faq_callback(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    raw = query.data or ""
    uid = query.from_user.id if query.from_user else 0
    lang = await _faq_lang(uid)

    if raw == "faq:close":
        try:
            await query.message.delete()
        except TelegramBadRequest:
            pass
        return

    if raw == "faq:list":
        faqs = await _active_faqs()
        if not faqs:
            try:
                await query.message.delete()
            except TelegramBadRequest:
                pass
            return
        list_title = msg(lang, "faq_list_title")
        try:
            await query.message.edit_text(
                list_title,
                reply_markup=faq_list_kb(faqs, lang),
            )
        except TelegramBadRequest:
            await query.message.answer(
                list_title,
                reply_markup=faq_list_kb(faqs, lang),
            )
        return

    try:
        faq_id = int(raw.split(":", 1)[1])
    except (ValueError, IndexError):
        return

    r = await db.execute(select(Faq).where(Faq.id == faq_id))
    faq = r.scalar_one_or_none()
    if not faq:
        await query.answer(msg(lang, "faq_not_found"), show_alert=True)
        return

    text = f"❓ <b>{escape(_faq_q(faq, lang))}</b>\n\n{escape(_faq_a(faq, lang))}"
    try:
        await query.message.edit_text(text, reply_markup=faq_detail_kb(lang))
    except TelegramBadRequest:
        await query.message.answer(text, reply_markup=faq_detail_kb(lang))
