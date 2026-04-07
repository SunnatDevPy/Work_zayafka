"""User-facing FAQ handler."""

from html import escape

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup
from sqlalchemy import select

from keyboards.inline import faq_detail_kb, faq_list_kb
from models.database import db
from models.faq import Faq

router = Router(name="faq")

USER_BTN_FAQ = "📋 Tez-tez so'raladigan savollar"


async def _active_faqs() -> list[Faq]:
    r = await db.execute(select(Faq).order_by(Faq.sort_order, Faq.id))
    return list(r.scalars().all())


# ─────────────────────────── Entry point ────────────────────────────

@router.message(F.text == USER_BTN_FAQ)
async def show_faq_list(message: Message, state: FSMContext) -> None:
    faqs = await _active_faqs()
    if not faqs:
        await message.answer(
            "📭 Hozircha FAQ qo'shilmagan.\n"
            "Administrator tez orada to'ldiradi."
        )
        return
    await message.answer(
        f"📋 <b>Tez-tez so'raladigan savollar</b>\n\n"
        f"Qiziqtirgan savolni tanlang 👇",
        reply_markup=faq_list_kb(faqs),
    )


# ─────────────────────────── Inline callbacks ───────────────────────

@router.callback_query(F.data.startswith("faq:"))
async def faq_callback(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    raw = query.data or ""

    # ── Close / back to main menu ──
    if raw == "faq:close":
        try:
            await query.message.delete()
        except TelegramBadRequest:
            pass
        return

    # ── Back to FAQ list ──
    if raw == "faq:list":
        faqs = await _active_faqs()
        if not faqs:
            try:
                await query.message.delete()
            except TelegramBadRequest:
                pass
            return
        try:
            await query.message.edit_text(
                "📋 <b>Tez-tez so'raladigan savollar</b>\n\nQiziqtirgan savolni tanlang 👇",
                reply_markup=faq_list_kb(faqs),
            )
        except TelegramBadRequest:
            await query.message.answer(
                "📋 <b>Tez-tez so'raladigan savollar</b>\n\nQiziqtirgan savolni tanlang 👇",
                reply_markup=faq_list_kb(faqs),
            )
        return

    # ── Show specific FAQ answer ──
    try:
        faq_id = int(raw.split(":", 1)[1])
    except (ValueError, IndexError):
        return

    r = await db.execute(select(Faq).where(Faq.id == faq_id))
    faq = r.scalar_one_or_none()
    if not faq:
        await query.answer("⚠️ Savol topilmadi.", show_alert=True)
        return

    text = (
        f"❓ <b>{escape(faq.question)}</b>\n\n"
        f"{escape(faq.answer)}"
    )
    try:
        await query.message.edit_text(text, reply_markup=faq_detail_kb())
    except TelegramBadRequest:
        await query.message.answer(text, reply_markup=faq_detail_kb())
