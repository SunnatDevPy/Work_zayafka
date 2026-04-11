from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from config import conf
from locales.messages import LANG_UZ, msg, norm_lang
from utils.user_locale import get_user_locale

router = Router(name="channel_review")

# Пустая клавиатура — Telegram снимает инлайн-кнопки с сообщения.
_NO_INLINE = InlineKeyboardMarkup(inline_keyboard=[])


def _is_admin(uid: int | None) -> bool:
    return uid is not None and uid in conf.bot.admin_ids


@router.callback_query(F.data.startswith("app:int:"))
async def application_interview(query: CallbackQuery) -> None:
    if not _is_admin(query.from_user.id if query.from_user else None):
        await query.answer("🔒 Faqat administratorlar uchun.", show_alert=True)
        return

    try:
        user_id = int((query.data or "").split(":", 2)[2])
    except (ValueError, IndexError):
        await query.answer("⚠️ Maʼlumot xatosi", show_alert=True)
        return

    await query.answer()

    loc = await get_user_locale(user_id)
    lg = norm_lang(loc) if loc else LANG_UZ

    try:
        await query.bot.send_message(
            user_id,
            msg(lg, "interview_user_msg"),
            parse_mode=ParseMode.HTML,
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

    append = "\n\n" + msg(lg, "channel_interview_sent")
    try:
        if query.message.document or query.message.photo:
            cap = (query.message.caption or "") + append
            if len(cap) > 1024:
                base = query.message.caption or ""
                cap = base[: max(0, 1024 - len(append))] + append
            await query.message.edit_caption(
                caption=cap,
                parse_mode=ParseMode.HTML,
                reply_markup=_NO_INLINE,
            )
        elif query.message.text is not None:
            txt = (query.message.text or "") + append
            await query.message.edit_text(
                txt,
                parse_mode=ParseMode.HTML,
                reply_markup=_NO_INLINE,
            )
        else:
            await query.message.edit_reply_markup(reply_markup=_NO_INLINE)
    except TelegramBadRequest:
        try:
            await query.message.edit_reply_markup(reply_markup=_NO_INLINE)
        except TelegramBadRequest:
            pass


@router.callback_query(F.data == "app:del")
async def application_delete(query: CallbackQuery) -> None:
    if not _is_admin(query.from_user.id if query.from_user else None):
        await query.answer("🔒 Faqat administratorlar uchun.", show_alert=True)
        return

    try:
        await query.bot.delete_message(query.message.chat.id, query.message.message_id)
        await query.answer("🗑 O‘chirildi")
    except TelegramBadRequest:
        try:
            await query.message.edit_reply_markup(reply_markup=_NO_INLINE)
        except TelegramBadRequest:
            pass
        await query.answer("❌ Xabarni o‘chirish mumkin emas.", show_alert=True)
