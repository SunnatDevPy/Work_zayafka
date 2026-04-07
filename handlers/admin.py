import asyncio

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import func, select

from config import conf
from keyboards.inline import (
    admin_faq_list_kb,
    admin_main_kb,
    faq_delete_confirm_kb,
    faq_edit_kb,
    vacancies_pick_kb,
    vacancy_admin_list_kb,
    vacancy_delete_confirm_kb,
    vacancy_edit_kb,
    yes_no_kb,
)
from models.bot_user import BotUser
from models.database import db
from models.faq import Faq
from models.question import Question
from models.vacancy import Vacancy
from utils.filters import AdminFilter

router = Router(name="admin")


class AdminVacancySG(StatesGroup):
    title = State()


class AdminVacancyEditSG(StatesGroup):
    title = State()
    description = State()


class AdminQuestionSG(StatesGroup):
    enter_text = State()
    choose_photo = State()


class BroadcastSG(StatesGroup):
    waiting = State()
    confirm = State()


class AdminFaqSG(StatesGroup):
    question   = State()
    answer     = State()
    edit_question = State()
    edit_answer   = State()


# ─────────────────────────── utils ──────────────────────────────────

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
        await query.message.answer(text, reply_markup=reply_markup)


async def _vacancy_edit_text(vid: int) -> tuple[str, bool]:
    """Returns (text, is_active) for vacancy edit menu."""
    v = await Vacancy.get_or_none(vid)
    if not v:
        return "⚠️ Vakansiya topilmadi.", False
    r = await db.execute(
        select(func.count()).select_from(Question).where(Question.vacancy_id == vid)
    )
    q_count = int(r.scalar() or 0)
    status = "✅ Faol" if v.is_active else "⏸ Nofaol"
    desc = v.description or "—"
    text = (
        f"💼 <b>{v.title}</b>\n\n"
        f"📄 Tavsif: {desc}\n"
        f"📊 Holat: {status}\n"
        f"❓ Savollar: {q_count} ta"
    )
    return text, v.is_active


# ─────────────────────────── Admin entry ────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    if not message.from_user or message.from_user.id not in conf.bot.admin_ids:
        await message.answer("🚫 Ruxsat yo'q.")
        return
    await state.clear()
    await message.answer("🛠 <b>Admin panel</b>", reply_markup=admin_main_kb())


# ─────────────────────────── Vacancy list ───────────────────────────

@router.callback_query(F.data == "adm:vac", AdminFilter())
async def adm_vac_list(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    r = await db.execute(select(Vacancy).order_by(Vacancy.sort_order, Vacancy.id))
    vacs = list(r.scalars().all())
    text = "💼 <b>Vakansiyalar ro'yxati:</b>" if vacs else "📭 Vakansiyalar hozircha yo'q."
    await _edit_or_answer(query, text, vacancy_admin_list_kb(vacs))


# ─────────────────────────── Vacancy add ────────────────────────────

@router.callback_query(F.data == "admva:add", AdminFilter())
async def adm_vac_add_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.set_state(AdminVacancySG.title)
    msg = await query.message.answer("✏️ Vakansiya nomini bitta xabar bilan yozing:")
    await state.update_data(prompt_msg_id=msg.message_id)


@router.message(AdminVacancySG.title, AdminFilter(), F.text)
async def adm_vac_add_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("⚠️ Nom bo'sh bo'lmasligi kerak.")
        return
    data = await state.get_data()
    await state.clear()

    r = await db.execute(select(func.coalesce(func.max(Vacancy.sort_order), 0)))
    mx = int(r.scalar() or 0)
    await Vacancy.create(title=title, description=None, sort_order=mx + 1, is_active=True)

    await _delete_msg(message.bot, message.chat.id, data.get("prompt_msg_id"))
    try:
        await message.delete()
    except Exception:
        pass

    r2 = await db.execute(select(Vacancy).order_by(Vacancy.sort_order, Vacancy.id))
    vacs = list(r2.scalars().all())
    await message.answer(
        f"✅ «{title}» qo'shildi.\n\n💼 <b>Vakansiyalar ro'yxati:</b>",
        reply_markup=vacancy_admin_list_kb(vacs),
    )


# ─────────────────────────── Vacancy edit menu ──────────────────────

@router.callback_query(F.data.startswith("admve:"), AdminFilter())
async def adm_ve_menu(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        vid = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    text, is_active = await _vacancy_edit_text(vid)
    await _edit_or_answer(query, text, vacancy_edit_kb(vid, is_active))


# ─────────────────────────── Edit title ─────────────────────────────

@router.callback_query(F.data.startswith("advt:"), AdminFilter())
async def adm_ve_title_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        vid = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    await state.set_state(AdminVacancyEditSG.title)
    msg = await query.message.answer("✏️ Vakansiyaning yangi nomini yozing:")
    await state.update_data(edit_vacancy_id=vid, prompt_msg_id=msg.message_id)


@router.message(AdminVacancyEditSG.title, AdminFilter(), F.text)
async def adm_ve_title_save(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("⚠️ Nom bo'sh bo'lmasligi kerak.")
        return
    data = await state.get_data()
    vid = data.get("edit_vacancy_id")
    await Vacancy.update(vid, title=title)
    await state.clear()

    await _delete_msg(message.bot, message.chat.id, data.get("prompt_msg_id"))
    try:
        await message.delete()
    except Exception:
        pass

    text, is_active = await _vacancy_edit_text(vid)
    await message.answer(f"✅ Nom yangilandi.\n\n{text}", reply_markup=vacancy_edit_kb(vid, is_active))


# ─────────────────────────── Edit description ───────────────────────

@router.callback_query(F.data.startswith("advd:"), AdminFilter())
async def adm_ve_desc_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        vid = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    await state.set_state(AdminVacancyEditSG.description)
    msg = await query.message.answer(
        "📝 Yangi tavsifni yozing.\n"
        "O'chirish uchun — belgisini yuboring."
    )
    await state.update_data(edit_vacancy_id=vid, prompt_msg_id=msg.message_id)


@router.message(AdminVacancyEditSG.description, AdminFilter(), F.text)
async def adm_ve_desc_save(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    vid = data.get("edit_vacancy_id")
    raw = (message.text or "").strip()
    new_desc: str | None = None if raw in ("-", "\u2014") else raw
    await Vacancy.update(vid, description=new_desc)
    await state.clear()

    await _delete_msg(message.bot, message.chat.id, data.get("prompt_msg_id"))
    try:
        await message.delete()
    except Exception:
        pass

    label = "yangilandi" if new_desc else "o'chirildi"
    text, is_active = await _vacancy_edit_text(vid)
    await message.answer(f"✅ Tavsif {label}.\n\n{text}", reply_markup=vacancy_edit_kb(vid, is_active))


# ─────────────────────────── Toggle active ──────────────────────────

@router.callback_query(F.data.startswith("adva:"), AdminFilter())
async def adm_ve_toggle(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        vid = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    v = await Vacancy.get_or_none(vid)
    if not v:
        return
    new_val = not v.is_active
    await Vacancy.update(vid, is_active=new_val)
    label = "faollashtirildi ✅" if new_val else "faolsizlashtirildi ⏸"
    text, _ = await _vacancy_edit_text(vid)
    await _edit_or_answer(query, f"💼 «{v.title}» {label}.\n\n{text}", vacancy_edit_kb(vid, new_val))


# ─────────────────────────── Delete vacancy ─────────────────────────

@router.callback_query(F.data.startswith("advdel:"), AdminFilter())
async def adm_ve_delete_confirm(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    raw = query.data or ""
    if raw.startswith("advdel_ok:"):
        return
    try:
        vid = int(raw.split(":", 1)[1])
    except (ValueError, IndexError):
        return
    v = await Vacancy.get_or_none(vid)
    if not v:
        return
    r = await db.execute(
        select(func.count()).select_from(Question).where(Question.vacancy_id == vid)
    )
    q_count = int(r.scalar() or 0)
    confirm_text = (
        f"🗑 <b>«{v.title}»</b> o'chirilsinmi?\n"
        f"⚠️ Unga bog'liq {q_count} ta savol ham o'chadi."
    )
    await _edit_or_answer(query, confirm_text, vacancy_delete_confirm_kb(vid))


@router.callback_query(F.data.startswith("advdel_ok:"), AdminFilter())
async def adm_ve_delete(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        vid = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    v = await Vacancy.get_or_none(vid)
    title = v.title if v else str(vid)
    await Vacancy.delete(vid)

    r = await db.execute(select(Vacancy).order_by(Vacancy.sort_order, Vacancy.id))
    vacs = list(r.scalars().all())
    list_text = "💼 <b>Vakansiyalar ro'yxati:</b>" if vacs else "📭 Vakansiyalar hozircha yo'q."
    await _edit_or_answer(query, f"✅ «{title}» o'chirildi.\n\n{list_text}", vacancy_admin_list_kb(vacs))


# ─────────────────────────── Questions menu ─────────────────────────

@router.callback_query(F.data == "adm:q", AdminFilter())
async def adm_q_menu(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    r = await db.execute(select(Vacancy).order_by(Vacancy.sort_order, Vacancy.id))
    vacs = list(r.scalars().all())
    if not vacs:
        await _edit_or_answer(query, "⚠️ Avval vakansiya qo'shing.")
        return
    await _edit_or_answer(query, "❓ Savollar uchun vakansiyani tanlang:", vacancies_pick_kb(vacs, "admq"))


@router.callback_query(F.data.startswith("admq:"), AdminFilter())
async def adm_q_vacancy(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    raw = query.data or ""
    if raw == "admq:back":
        await _edit_or_answer(query, "🛠 <b>Admin panel</b>", admin_main_kb())
        return
    try:
        vid = int(raw.split(":", 1)[1])
    except (ValueError, IndexError):
        return

    v = await Vacancy.get_or_none(vid)
    if not v:
        await query.message.answer("⚠️ Vakansiya topilmadi.")
        return

    r = await db.execute(
        select(Question).where(Question.vacancy_id == vid).order_by(Question.sort_order, Question.id)
    )
    qs = list(r.scalars().all())
    lines = [
        f"{q.id}. [{q.sort_order}] {'📷' if q.require_photo else '📝'} {q.text[:80]}{'…' if len(q.text) > 80 else ''}"
        for q in qs
    ]
    text = f"💼 <b>{v.title}</b>\n\n❓ Savollar:\n" + ("\n".join(lines) if lines else "— hozircha yo'q")

    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="➕ Savol qo'shish", callback_data=f"adqq:{vid}"))
    for q in qs:
        icon = "📷" if q.require_photo else "📝"
        b.row(InlineKeyboardButton(text=f"{icon} #{q.id} — {q.text[:28]}", callback_data=f"adqe:{q.id}"))
    b.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admve:{vid}"))
    await _edit_or_answer(query, text, b.as_markup())


# ─────────────────────────── Question add ───────────────────────────

@router.callback_query(F.data.startswith("adqq:"), AdminFilter())
async def adm_q_add_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        vid = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    await state.set_state(AdminQuestionSG.enter_text)
    msg = await query.message.answer("✏️ Savol matnini bitta xabar bilan yozing:")
    await state.update_data(vacancy_id=vid, prompt_msg_id=msg.message_id)


@router.message(AdminQuestionSG.enter_text, AdminFilter(), F.text)
async def adm_q_enter_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    edit_qid = data.get("edit_question_id")
    text = (message.text or "").strip()
    if not text:
        await message.answer("⚠️ Matn bo'sh bo'lmasligi kerak.")
        return

    await _delete_msg(message.bot, message.chat.id, data.get("prompt_msg_id"))
    try:
        await message.delete()
    except Exception:
        pass

    if edit_qid:
        await Question.update(edit_qid, text=text)
        await state.clear()
        await message.answer("✅ Savol matni yangilandi.")
        return

    await state.update_data(question_text=text)
    await state.set_state(AdminQuestionSG.choose_photo)
    prompt = await message.answer("📷 Nomzoddan rasm talab qilinsinmi?", reply_markup=yes_no_kb("qconf"))
    await state.update_data(prompt_msg_id=prompt.message_id)


@router.callback_query(
    F.data.startswith("qconf:"),
    AdminFilter(),
    StateFilter(AdminQuestionSG.choose_photo),
)
async def adm_q_add_confirm(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    flag = (query.data or "").endswith(":1")
    data = await state.get_data()
    vid = data.get("vacancy_id")
    qtext = data.get("question_text")
    if not vid or not qtext:
        await query.message.answer("⚠️ Sessiya tugadi. Qaytadan boshlang.")
        await state.clear()
        return

    r = await db.execute(
        select(func.coalesce(func.max(Question.sort_order), 0)).where(Question.vacancy_id == vid)
    )
    mx = int(r.scalar() or 0)
    await Question.create(vacancy_id=vid, text=qtext, sort_order=mx + 1, require_photo=flag)
    await state.clear()

    req_text = "ha" if flag else "yo'q"
    await _edit_or_answer(query, f"✅ Savol qo'shildi (rasm: {req_text}).")


# ─────────────────────────── Question edit ──────────────────────────

@router.callback_query(F.data.startswith("adqe:"), AdminFilter())
async def adm_q_edit_menu(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        qid = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    q = await Question.get_or_none(qid)
    if not q:
        await query.message.answer("⚠️ Savol topilmadi.")
        return
    v = await Vacancy.get_or_none(q.vacancy_id)

    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="✏️ Matnni o'zgartirish",      callback_data=f"adqt:{qid}"))
    b.row(InlineKeyboardButton(text="📷 Rasm talabini o'zgartirish", callback_data=f"adqf:{qid}"))
    b.row(InlineKeyboardButton(text="🗑 O'chirish",                 callback_data=f"adqd:{qid}"))
    b.row(InlineKeyboardButton(text="⬅️ Orqaga",                   callback_data=f"admq:{q.vacancy_id}"))

    title = v.title if v else str(q.vacancy_id)
    req_text = "ha" if q.require_photo else "yo'q"
    await _edit_or_answer(
        query,
        f"💼 {title}\n\n❓ Savol:\n{q.text}\n\n📷 Rasm majburiy: {req_text}",
        b.as_markup(),
    )


@router.callback_query(F.data.startswith("adqt:"), AdminFilter())
async def adm_q_edit_text_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        qid = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    await state.set_state(AdminQuestionSG.enter_text)
    msg = await query.message.answer("✏️ Savolning yangi matnini yozing:")
    await state.update_data(edit_question_id=qid, prompt_msg_id=msg.message_id)


@router.callback_query(F.data.startswith("adqf:"), AdminFilter())
async def adm_q_toggle_photo(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        qid = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    q = await Question.get_or_none(qid)
    if not q:
        return
    new_val = not q.require_photo
    await Question.update(qid, require_photo=new_val)
    v = await Vacancy.get_or_none(q.vacancy_id)

    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="✏️ Matnni o'zgartirish",      callback_data=f"adqt:{qid}"))
    b.row(InlineKeyboardButton(text="📷 Rasm talabini o'zgartirish", callback_data=f"adqf:{qid}"))
    b.row(InlineKeyboardButton(text="🗑 O'chirish",                 callback_data=f"adqd:{qid}"))
    b.row(InlineKeyboardButton(text="⬅️ Orqaga",                   callback_data=f"admq:{q.vacancy_id}"))

    title = v.title if v else str(q.vacancy_id)
    req_text = "ha" if new_val else "yo'q"
    await _edit_or_answer(
        query,
        f"💼 {title}\n\n❓ Savol:\n{q.text}\n\n📷 Rasm majburiy: {req_text} (yangilandi)",
        b.as_markup(),
    )


@router.callback_query(F.data.startswith("adqd:"), AdminFilter())
async def adm_q_delete(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        qid = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    q = await Question.get_or_none(qid)
    vid = q.vacancy_id if q else None
    await Question.delete(qid)
    await _edit_or_answer(query, "🗑 Savol o'chirildi.")


# ─────────────────────────── FAQ list ───────────────────────────────

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
    await _edit_or_answer(query, "🛠 <b>Admin panel</b>", admin_main_kb())


# ─────────────────────────── FAQ add ────────────────────────────────

@router.callback_query(F.data == "admfa:add", AdminFilter())
async def adm_faq_add_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.set_state(AdminFaqSG.question)
    msg = await query.message.answer("✏️ Savol matnini yozing (foydalanuvchiga ko'rinadigan):")
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
    await state.update_data(faq_question=question)
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
    question = data.get("faq_question", "")

    await _delete_msg(message.bot, message.chat.id, data.get("prompt_msg_id"))
    try:
        await message.delete()
    except Exception:
        pass

    r = await db.execute(select(func.coalesce(func.max(Faq.sort_order), 0)))
    mx = int(r.scalar() or 0)
    await Faq.create(question=question, answer=answer, sort_order=mx + 1)
    await state.clear()

    r2 = await db.execute(select(Faq).order_by(Faq.sort_order, Faq.id))
    faqs = list(r2.scalars().all())
    await message.answer(
        "✅ FAQ qo'shildi.\n\n📋 <b>FAQ ro'yxati:</b>",
        reply_markup=admin_faq_list_kb(faqs),
    )


# ─────────────────────────── FAQ edit menu ──────────────────────────

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
        f"❓ <b>Savol:</b>\n{esc(faq.question)}\n\n"
        f"💬 <b>Javob:</b>\n{esc(faq.answer)}"
    )
    await _edit_or_answer(query, text, faq_edit_kb(faq_id))


# ─────────────────────────── FAQ edit question ──────────────────────

@router.callback_query(F.data.startswith("admfq:"), AdminFilter())
async def adm_faq_edit_q_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        faq_id = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    await state.set_state(AdminFaqSG.edit_question)
    msg = await query.message.answer("✏️ Yangi savol matnini yozing:")
    await state.update_data(edit_faq_id=faq_id, prompt_msg_id=msg.message_id)


@router.message(AdminFaqSG.edit_question, AdminFilter(), F.text)
async def adm_faq_edit_q_save(message: Message, state: FSMContext) -> None:
    question = (message.text or "").strip()
    if not question:
        await message.answer("⚠️ Savol bo'sh bo'lmasligi kerak.")
        return
    data = await state.get_data()
    faq_id = data.get("edit_faq_id")
    await Faq.update(faq_id, question=question)
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
        f"❓ <b>Savol:</b>\n{esc(faq.question) if faq else ''}\n\n"
        f"💬 <b>Javob:</b>\n{esc(faq.answer) if faq else ''}"
    )
    await message.answer(text, reply_markup=faq_edit_kb(faq_id))


# ─────────────────────────── FAQ edit answer ────────────────────────

@router.callback_query(F.data.startswith("admfa_ans:"), AdminFilter())
async def adm_faq_edit_a_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        faq_id = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    await state.set_state(AdminFaqSG.edit_answer)
    msg = await query.message.answer("✏️ Yangi javobni yozing:")
    await state.update_data(edit_faq_id=faq_id, prompt_msg_id=msg.message_id)


@router.message(AdminFaqSG.edit_answer, AdminFilter(), F.text)
async def adm_faq_edit_a_save(message: Message, state: FSMContext) -> None:
    answer = (message.text or "").strip()
    if not answer:
        await message.answer("⚠️ Javob bo'sh bo'lmasligi kerak.")
        return
    data = await state.get_data()
    faq_id = data.get("edit_faq_id")
    await Faq.update(faq_id, answer=answer)
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
        f"❓ <b>Savol:</b>\n{esc(faq.question) if faq else ''}\n\n"
        f"💬 <b>Javob:</b>\n{esc(faq.answer) if faq else ''}"
    )
    await message.answer(text, reply_markup=faq_edit_kb(faq_id))


# ─────────────────────────── FAQ delete ─────────────────────────────

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
        f"🗑 <b>«{esc(faq.question[:60])}»</b>\n\nO'chirishni tasdiqlaysizmi?",
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


# ─────────────────────────── Broadcast ──────────────────────────────

@router.callback_query(F.data == "adm:bc", AdminFilter())
async def adm_bc_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.set_state(BroadcastSG.waiting)
    r = await db.execute(select(func.count()).select_from(BotUser))
    n = int(r.scalar() or 0)
    await _edit_or_answer(
        query,
        f"📢 Keyingi xabaringiz <b>{n} ta</b> foydalanuvchiga yuboriladi.\n"
        f"Xabarni yuboring (matn, rasm, video …).",
    )


@router.message(BroadcastSG.waiting, AdminFilter())
async def adm_bc_receive(message: Message, state: FSMContext) -> None:
    await state.update_data(bc_chat_id=message.chat.id, bc_message_id=message.message_id)
    await state.set_state(BroadcastSG.confirm)
    from keyboards.inline import broadcast_confirm_kb
    await message.answer("📤 Bu xabarni hammaga yuboraylikmi?", reply_markup=broadcast_confirm_kb())


@router.callback_query(F.data == "bc:cancel", AdminFilter())
async def adm_bc_cancel(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer("❌ Bekor qilindi")
    await state.clear()
    await _edit_or_answer(query, "❌ Reklama bekor qilindi.")


@router.callback_query(F.data == "bc:send", AdminFilter(), StateFilter(BroadcastSG.confirm))
async def adm_bc_send(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer("📤 Yuborilmoqda…")
    data = await state.get_data()
    chat_id = data.get("bc_chat_id")
    mid = data.get("bc_message_id")
    await state.clear()
    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    if not chat_id or not mid:
        await query.message.answer("⚠️ Yuborish uchun ma'lumot yo'q.")
        return

    r = await db.execute(select(BotUser.telegram_id))
    ids = list(r.scalars().all())
    ok = fail = 0
    for uid in ids:
        try:
            await query.bot.copy_message(chat_id=uid, from_chat_id=chat_id, message_id=mid)
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.04)
    await query.message.answer(f"✅ Tayyor: yuborildi {ok}, xato {fail}.")
