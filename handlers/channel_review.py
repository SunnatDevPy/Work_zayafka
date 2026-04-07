import os

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery, FSInputFile

from config import conf
from keyboards.inline import homework_invite_kb

router = Router(name="channel_review")


def _is_admin(uid: int | None) -> bool:
    return uid is not None and uid in conf.bot.admin_ids


@router.callback_query(F.data.startswith("app:ok:"))
async def application_accept(query: CallbackQuery) -> None:
    if not _is_admin(query.from_user.id if query.from_user else None):
        await query.answer("🔒 Faqat administratorlar uchun.", show_alert=True)
        return

    try:
        user_id = int((query.data or "").split(":", 2)[2])
    except (ValueError, IndexError):
        await query.answer("⚠️ Ma'lumot xatosi", show_alert=True)
        return

    await query.answer()

    bot = query.bot
    text = conf.bot.homework_invite_text()
    pdf_path = conf.bot.homework_pdf_path()

    try:
        await bot.send_message(
            user_id,
            text,
            reply_markup=homework_invite_kb(),
            parse_mode=ParseMode.HTML,
        )
        if pdf_path and os.path.isfile(pdf_path):
            await bot.send_document(
                user_id,
                FSInputFile(pdf_path, filename=os.path.basename(pdf_path)),
                caption="📎 Test vazifasi (PDF).",
            )
    except TelegramForbiddenError:
        await query.answer(
            "⚠️ Foydalanuvchi botni ishga tushirmagan yoki bloklagan.",
            show_alert=True,
        )
        return
    except TelegramBadRequest as e:
        await query.answer(f"❌ Xato: {e}", show_alert=True)
        return

    try:
        cap = (query.message.caption or "") + "\n\n✅ Qabul qilindi — nomzodga vazifa yuborildi."
        if len(cap) > 1024:
            cap = (query.message.caption or "")[:900] + "\n\n✅ Qabul qilindi."
        await query.message.edit_caption(caption=cap, parse_mode=ParseMode.HTML)
    except TelegramBadRequest:
        try:
            await query.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass


@router.callback_query(F.data == "app:del")
async def application_delete(query: CallbackQuery) -> None:
    if not _is_admin(query.from_user.id if query.from_user else None):
        await query.answer("🔒 Faqat administratorlar uchun.", show_alert=True)
        return

    await query.answer("🗑 O‘chirildi")
    try:
        await query.bot.delete_message(query.message.chat.id, query.message.message_id)
    except TelegramBadRequest:
        await query.answer("❌ Xabarni o‘chirish mumkin emas.", show_alert=True)
