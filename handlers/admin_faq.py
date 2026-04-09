from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select

from keyboards.inline import admin_faq_list_kb, admin_main_kb, faq_delete_confirm_kb, faq_edit_kb
from models.database import db
from models.faq import Faq
from utils.filters import AdminFilter
from utils.user_locale import get_user_locale
from locales.messages import LANG_UZ, norm_lang

router = Router(name="admin_faq")


async def _admin_lang(uid: int | None) -> str:
    if not uid:
        return LANG_UZ
    loc = await get_user_locale(uid)
    return norm_lang(loc) if loc else LANG_UZ


class AdminFaqSG(StatesGroup):
    question = State()
    answer = State()
    edit_question = State()
    edit_answer = State()


def _split_bilingual(raw: str) -> tuple[str, str]:
    if "/" in raw:
        ru, uz = raw.split("/", 1)
        ru = ru.strip()
        uz = uz.strip()
        return (ru or uz), (uz or ru)
    if "|" in raw:
        ru, uz = raw.split("|", 1)
        ru = ru.strip()
        uz = uz.strip()
        return (ru or uz), (uz or ru)
    text = raw.strip()
    return text, text


async def _delete_msg(bot, chat_id: int, msg_id: int | None) -> None:
    if not msg_id:
        return
    try:
        await bot.delete_message(chat_id, msg_id)
    except Exception:
        pass


async def _edit_or_answer(query: CallbackQuery, text: str, reply_markup=None) -> None:
    try:
        await query.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        try:
            await query.message.delete()
        except Exception:
            pass
        await query.message.answer(text, reply_markup=reply_markup)


@router.callback_query(F.data == "adm:faq", AdminFilter())
async def adm_faq_list(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    r = await db.execute(select(Faq).order_by(Faq.sort_order, Faq.id))
    faqs = list(r.scalars().all())
    text = "📋 <b>FAQ ro'yxati:</b>" if faqs else "📭 FAQ hozircha yo'q. ➕ qo'shing."
    await _edit_or_answer(query, text, admin_faq_list_kb(faqs))


@router.callback_query(F.data == "admfa:back", AdminFilter())
async def adm_faq_back(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    lang = await _admin_lang(query.from_user.id if query.from_user else None)
    await _edit_or_answer(query, "🛠 <b>Admin panel</b>", admin_main_kb(lang))


@router.callback_query(F.data == "admfa:add", AdminFilter())
async def adm_faq_add_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.set_state(AdminFaqSG.question)
    msg = await query.message.answer("✏️ Savol matnini yozing.\nFormat: RU / UZ")
    await state.update_data(prompt_msg_id=msg.message_id)


@router.message(AdminFaqSG.question, AdminFilter(), F.text)
async def adm_faq_enter_question(message: Message, state: FSMContext) -> None:
    question = (message.text or "").strip()
    if not question:
        await message.answer("⚠️ Savol bo'sh bo'lmasligi kerak.")
        return
    data = await state.get_data()
    await _delete_msg(message.bot, message.chat.id, data.get("prompt_msg_id"))
    try:
        await message.delete()
    except Exception:
        pass
    q_ru, q_uz = _split_bilingual(question)
    await state.update_data(faq_question_ru=q_ru, faq_question_uz=q_uz)
    await state.set_state(AdminFaqSG.answer)
    msg = await message.answer(
        f"✅ Savol: <i>{question}</i>\n\n"
        "📝 Endi javobni yozing:"
    )
    await state.update_data(prompt_msg_id=msg.message_id)


@router.message(AdminFaqSG.answer, AdminFilter(), F.text)
async def adm_faq_enter_answer(message: Message, state: FSMContext) -> None:
    answer = (message.text or "").strip()
    if not answer:
        await message.answer("⚠️ Javob bo'sh bo'lmasligi kerak.")
        return
    data = await state.get_data()
    question_ru = data.get("faq_question_ru", "")
    question_uz = data.get("faq_question_uz", "")

    await _delete_msg(message.bot, message.chat.id, data.get("prompt_msg_id"))
    try:
        await message.delete()
    except Exception:
        pass

    r = await db.execute(select(func.coalesce(func.max(Faq.sort_order), 0)))
    mx = int(r.scalar() or 0)
    a_ru, a_uz = _split_bilingual(answer)
    await Faq.create(
        question=question_ru,
        question_ru=question_ru,
        question_uz=question_uz or question_ru,
        answer=a_ru,
        answer_ru=a_ru,
        answer_uz=a_uz or a_ru,
        sort_order=mx + 1,
    )
    await state.clear()

    r2 = await db.execute(select(Faq).order_by(Faq.sort_order, Faq.id))
    faqs = list(r2.scalars().all())
    await message.answer(
        "✅ FAQ qo'shildi.\n\n📋 <b>FAQ ro'yxati:</b>",
        reply_markup=admin_faq_list_kb(faqs),
    )


@router.callback_query(F.data.startswith("admfe:"), AdminFilter())
async def adm_faq_edit_menu(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        faq_id = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    r = await db.execute(select(Faq).where(Faq.id == faq_id))
    faq = r.scalar_one_or_none()
    if not faq:
        await query.message.answer("⚠️ FAQ topilmadi.")
        return
    from html import escape as esc
    text = (
        f"📋 <b>FAQ #{faq.id}</b>\n\n"
        f"❓ <b>Savol (RU/UZ):</b>\n{esc(faq.question_ru or faq.question or '')} | {esc(faq.question_uz or faq.question or '')}\n\n"
        f"💬 <b>Javob (RU/UZ):</b>\n{esc(faq.answer_ru or faq.answer or '')} | {esc(faq.answer_uz or faq.answer or '')}"
    )
    await _edit_or_answer(query, text, faq_edit_kb(faq_id))


@router.callback_query(F.data.startswith("admfq:"), AdminFilter())
async def adm_faq_edit_q_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        faq_id = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    await state.set_state(AdminFaqSG.edit_question)
    msg = await query.message.answer("✏️ Yangi savol matnini yozing.\nFormat: RU / UZ")
    await state.update_data(edit_faq_id=faq_id, prompt_msg_id=msg.message_id)


@router.message(AdminFaqSG.edit_question, AdminFilter(), F.text)
async def adm_faq_edit_q_save(message: Message, state: FSMContext) -> None:
    question = (message.text or "").strip()
    if not question:
        await message.answer("⚠️ Savol bo'sh bo'lmasligi kerak.")
        return
    data = await state.get_data()
    faq_id = data.get("edit_faq_id")
    q_ru, q_uz = _split_bilingual(question)
    await Faq.update(faq_id, question=q_ru, question_ru=q_ru, question_uz=q_uz)
    await state.clear()

    await _delete_msg(message.bot, message.chat.id, data.get("prompt_msg_id"))
    try:
        await message.delete()
    except Exception:
        pass

    r = await db.execute(select(Faq).where(Faq.id == faq_id))
    faq = r.scalar_one_or_none()
    from html import escape as esc
    text = (
        f"✅ Savol yangilandi.\n\n"
        f"📋 <b>FAQ #{faq_id}</b>\n\n"
        f"❓ <b>Savol (RU/UZ):</b>\n{esc((faq.question_ru or faq.question) if faq else '')} | {esc((faq.question_uz or faq.question) if faq else '')}\n\n"
        f"💬 <b>Javob (RU/UZ):</b>\n{esc((faq.answer_ru or faq.answer) if faq else '')} | {esc((faq.answer_uz or faq.answer) if faq else '')}"
    )
    await message.answer(text, reply_markup=faq_edit_kb(faq_id))


@router.callback_query(F.data.startswith("admfa_ans:"), AdminFilter())
async def adm_faq_edit_a_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        faq_id = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    await state.set_state(AdminFaqSG.edit_answer)
    msg = await query.message.answer("✏️ Yangi javobni yozing.\nFormat: RU / UZ")
    await state.update_data(edit_faq_id=faq_id, prompt_msg_id=msg.message_id)


@router.message(AdminFaqSG.edit_answer, AdminFilter(), F.text)
async def adm_faq_edit_a_save(message: Message, state: FSMContext) -> None:
    answer = (message.text or "").strip()
    if not answer:
        await message.answer("⚠️ Javob bo'sh bo'lmasligi kerak.")
        return
    data = await state.get_data()
    faq_id = data.get("edit_faq_id")
    a_ru, a_uz = _split_bilingual(answer)
    await Faq.update(faq_id, answer=a_ru, answer_ru=a_ru, answer_uz=a_uz)
    await state.clear()

    await _delete_msg(message.bot, message.chat.id, data.get("prompt_msg_id"))
    try:
        await message.delete()
    except Exception:
        pass

    r = await db.execute(select(Faq).where(Faq.id == faq_id))
    faq = r.scalar_one_or_none()
    from html import escape as esc
    text = (
        f"✅ Javob yangilandi.\n\n"
        f"📋 <b>FAQ #{faq_id}</b>\n\n"
        f"❓ <b>Savol (RU/UZ):</b>\n{esc((faq.question_ru or faq.question) if faq else '')} | {esc((faq.question_uz or faq.question) if faq else '')}\n\n"
        f"💬 <b>Javob (RU/UZ):</b>\n{esc((faq.answer_ru or faq.answer) if faq else '')} | {esc((faq.answer_uz or faq.answer) if faq else '')}"
    )
    await message.answer(text, reply_markup=faq_edit_kb(faq_id))


@router.callback_query(F.data.startswith("admfd:"), AdminFilter())
async def adm_faq_delete_confirm(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    raw = query.data or ""
    if raw.startswith("admfd_ok:"):
        return
    try:
        faq_id = int(raw.split(":", 1)[1])
    except (ValueError, IndexError):
        return
    r = await db.execute(select(Faq).where(Faq.id == faq_id))
    faq = r.scalar_one_or_none()
    if not faq:
        return
    from html import escape as esc
    await _edit_or_answer(
        query,
        f"🗑 <b>«{esc((faq.question_ru or faq.question)[:60])}»</b>\n\nO'chirishni tasdiqlaysizmi?",
        faq_delete_confirm_kb(faq_id),
    )


@router.callback_query(F.data.startswith("admfd_ok:"), AdminFilter())
async def adm_faq_delete(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        faq_id = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    await Faq.delete(faq_id)

    r = await db.execute(select(Faq).order_by(Faq.sort_order, Faq.id))
    faqs = list(r.scalars().all())
    list_text = "📋 <b>FAQ ro'yxati:</b>" if faqs else "📭 FAQ hozircha yo'q."
    await _edit_or_answer(query, f"✅ FAQ o'chirildi.\n\n{list_text}", admin_faq_list_kb(faqs))

