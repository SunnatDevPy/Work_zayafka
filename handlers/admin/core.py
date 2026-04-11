from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import func, select

from config import conf
from keyboards.inline import (
    admin_main_kb,
    vacancy_admin_list_kb,
    vacancy_delete_confirm_kb,
    vacancy_edit_kb,
)
from models.bot_user import BotUser
from models.database import db
from models.vacancy import Vacancy
from utils.filters import AdminFilter
from utils.user_locale import get_user_locale, norm_lang
from locales.messages import LANG_UZ, msg

router = Router(name="admin")
_admin_panel_msg_by_user: dict[int, int] = {}


class AdminVacancyNewSG(StatesGroup):
    title = State()
    description = State()


class AdminVacancyEditSG(StatesGroup):
    title = State()
    description = State()


async def _admin_lang(uid: int | None) -> str:
    if not uid:
        return LANG_UZ
    loc = await get_user_locale(uid)
    return norm_lang(loc) if loc else LANG_UZ


async def _user_count() -> int:
    r = await db.execute(select(func.count()).select_from(BotUser))
    return int(r.scalar() or 0)


def _panel_text(n: int) -> str:
    return f"🛠 <b>Admin panel</b>\n\n👥 <b>Foydalanuvchilar / Пользователи:</b> {n}"


def _vacancy_line_title(v: Vacancy) -> str:
    a = (v.title_ru or v.title or "").strip()
    b = (v.title_uz or v.title or "").strip()
    if not a and not b:
        return "—"
    if a == b:
        return a
    return f"{a} / {b}"


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


async def _edit_or_answer(query: CallbackQuery, text: str, reply_markup=None) -> None:
    try:
        await query.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        try:
            await query.message.delete()
        except Exception:
            pass
        await query.message.answer(text, reply_markup=reply_markup)


async def _delete_msg(bot, chat_id: int, msg_id: int | None) -> None:
    if not msg_id:
        return
    try:
        await bot.delete_message(chat_id, msg_id)
    except Exception:
        pass


async def _send_prompt_and_track(state: FSMContext, message: Message, text: str, reply_markup=None) -> None:
    data = await state.get_data()
    await _delete_msg(message.bot, message.chat.id, data.get("prompt_msg_id"))
    sent = await message.answer(text, reply_markup=reply_markup)
    await state.update_data(prompt_msg_id=sent.message_id)


async def _send_prompt_from_query(
    state: FSMContext, query: CallbackQuery, text: str, reply_markup=None
) -> None:
    data = await state.get_data()
    await _delete_msg(query.bot, query.message.chat.id, data.get("prompt_msg_id"))
    sent = await query.message.answer(text, reply_markup=reply_markup)
    await state.update_data(prompt_msg_id=sent.message_id)


def _stop_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="⛔️ Bekor / Отмена", callback_data="admstop"))
    return b.as_markup()


def _back_kb(callback_data: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="⬅️ Orqaga / Назад", callback_data=callback_data))
    return b.as_markup()


async def _vacancy_edit_text(vid: int) -> tuple[str, bool]:
    v = await Vacancy.get_or_none(vid)
    if not v:
        return "⚠️ Vakansiya topilmadi.", False
    status = "✅ Faol" if v.is_active else "⏸ Nofaol"
    title_ru = (v.title_ru or v.title or "").strip() or "—"
    title_uz = (v.title_uz or v.title or "").strip() or "—"
    desc_ru = (v.description_ru or v.description or "").strip() or "—"
    desc_uz = (v.description_uz or v.description or "").strip() or "—"
    text = (
        f"💼 <b>{title_ru} / {title_uz}</b>\n\n"
        f"📄 Tavsif (RU): {desc_ru}\n"
        f"📄 Tavsif (UZ): {desc_uz}\n"
        f"📊 Holat: {status}"
    )
    return text, v.is_active


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    if not message.from_user or message.from_user.id not in conf.bot.admin_ids:
        await message.answer("🚫 Ruxsat yo'q.")
        return
    await state.clear()
    lang = await _admin_lang(message.from_user.id if message.from_user else None)
    prev_mid = _admin_panel_msg_by_user.get(message.from_user.id) if message.from_user else None
    if prev_mid:
        try:
            await message.bot.delete_message(message.chat.id, prev_mid)
        except Exception:
            pass
    n = await _user_count()
    await message.answer("🛠 Admin rejimi", reply_markup=ReplyKeyboardRemove())
    panel = await message.answer(_panel_text(n), reply_markup=admin_main_kb(lang))
    if message.from_user:
        _admin_panel_msg_by_user[message.from_user.id] = panel.message_id


@router.callback_query(F.data == "adm:vac", AdminFilter())
async def adm_vac_list(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.clear()
    r = await db.execute(select(Vacancy).order_by(Vacancy.sort_order, Vacancy.id))
    vacs = list(r.scalars().all())
    text = "💼 <b>Vakansiyalar:</b>" if vacs else "📭 Hozircha vakansiya yo'q."
    await _edit_or_answer(query, text, vacancy_admin_list_kb(vacs))


@router.callback_query(F.data == "admva:add", AdminFilter())
async def adm_vac_add_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.set_state(AdminVacancyNewSG.title)
    await _send_prompt_from_query(
        state,
        query,
        "✏️ <b>Vakansiya nomi</b>\nFormat: <code>RU matn / UZ matn</code>",
        reply_markup=_back_kb("admback:vac_list"),
    )


@router.message(AdminVacancyNewSG.title, AdminFilter(), F.text)
async def adm_vac_add_title(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw:
        await message.answer("⚠️ Bo'sh bo'lmasin.")
        return
    title_ru, title_uz = _split_bilingual(raw)
    if not title_ru:
        await message.answer("⚠️ Nom noto'g'ri.")
        return
    await state.update_data(new_title_ru=title_ru, new_title_uz=title_uz)
    await state.set_state(AdminVacancyNewSG.description)
    data = await state.get_data()
    await _delete_msg(message.bot, message.chat.id, data.get("prompt_msg_id"))
    try:
        await message.delete()
    except Exception:
        pass
    await _send_prompt_and_track(
        state,
        message,
        "📝 <b>Tavsif</b> (ixtiyoriy)\nFormat: <code>RU matn / UZ matn</code>\n"
        "O'tkazib yuborish uchun — <code>-</code> yuboring.",
        reply_markup=_back_kb("admback:vac_list"),
    )


@router.message(AdminVacancyNewSG.description, AdminFilter(), F.text)
async def adm_vac_add_description(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    title_ru = data.get("new_title_ru")
    title_uz = data.get("new_title_uz")
    if not title_ru:
        await state.clear()
        return
    raw = (message.text or "").strip()
    if raw in ("-", "—"):
        d_ru, d_uz = None, None
        desc_base = None
    else:
        d_ru, d_uz = _split_bilingual(raw)
        desc_base = d_ru

    r = await db.execute(select(func.coalesce(func.max(Vacancy.sort_order), 0)))
    mx = int(r.scalar() or 0)
    await Vacancy.create(
        title=title_ru,
        title_ru=title_ru,
        title_uz=title_uz,
        description=desc_base,
        description_ru=d_ru,
        description_uz=d_uz,
        sort_order=mx + 1,
        is_active=True,
    )
    await _delete_msg(message.bot, message.chat.id, data.get("prompt_msg_id"))
    await state.clear()
    try:
        await message.delete()
    except Exception:
        pass

    r2 = await db.execute(select(Vacancy).order_by(Vacancy.sort_order, Vacancy.id))
    vacs = list(r2.scalars().all())
    await message.answer(
        f"✅ Vakansiya qo'shildi.\n\n💼 <b>Vakansiyalar:</b>",
        reply_markup=vacancy_admin_list_kb(vacs),
    )


@router.callback_query(F.data.startswith("admve:"), AdminFilter())
async def adm_ve_menu(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        vid = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    text, is_active = await _vacancy_edit_text(vid)
    await _edit_or_answer(query, text, vacancy_edit_kb(vid, is_active))


@router.callback_query(F.data.startswith("advt:"), AdminFilter())
async def adm_ve_title_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        vid = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    await state.set_state(AdminVacancyEditSG.title)
    await state.update_data(edit_vacancy_id=vid)
    await _send_prompt_from_query(
        state,
        query,
        "✏️ Yangi nom\nFormat: <code>RU / UZ</code>",
        reply_markup=_back_kb(f"admback:vac_edit:{vid}"),
    )
    try:
        await query.message.delete()
    except Exception:
        pass


@router.message(AdminVacancyEditSG.title, AdminFilter(), F.text)
async def adm_ve_title_save(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("⚠️ Nom bo'sh.")
        return
    data = await state.get_data()
    vid = data.get("edit_vacancy_id")
    title_ru, title_uz = _split_bilingual(title)
    await Vacancy.update(vid, title=title_ru, title_ru=title_ru, title_uz=title_uz)
    await _delete_msg(message.bot, message.chat.id, data.get("prompt_msg_id"))
    await state.clear()
    try:
        await message.delete()
    except Exception:
        pass
    text, is_active = await _vacancy_edit_text(vid)
    await message.answer(f"✅ Nom yangilandi.\n\n{text}", reply_markup=vacancy_edit_kb(vid, is_active))


@router.callback_query(F.data.startswith("advd:"), AdminFilter())
async def adm_ve_desc_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        vid = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    await state.set_state(AdminVacancyEditSG.description)
    await state.update_data(edit_vacancy_id=vid)
    await _send_prompt_from_query(
        state,
        query,
        "📝 Yangi tavsif\nFormat: <code>RU / UZ</code>\nO'chirish: <code>-</code>",
        reply_markup=_back_kb(f"admback:vac_edit:{vid}"),
    )
    try:
        await query.message.delete()
    except Exception:
        pass


@router.message(AdminVacancyEditSG.description, AdminFilter(), F.text)
async def adm_ve_desc_save(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    vid = data.get("edit_vacancy_id")
    raw = (message.text or "").strip()
    if raw in ("-", "—"):
        await Vacancy.update(vid, description=None, description_ru=None, description_uz=None)
        new_desc = None
    else:
        d_ru, d_uz = _split_bilingual(raw)
        await Vacancy.update(vid, description=d_ru, description_ru=d_ru, description_uz=d_uz)
        new_desc = raw
    await _delete_msg(message.bot, message.chat.id, data.get("prompt_msg_id"))
    await state.clear()
    try:
        await message.delete()
    except Exception:
        pass
    label = "yangilandi" if new_desc else "o'chirildi"
    text, is_active = await _vacancy_edit_text(vid)
    await message.answer(f"✅ Tavsif {label}.\n\n{text}", reply_markup=vacancy_edit_kb(vid, is_active))


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
    await _edit_or_answer(
        query,
        f"💼 «{_vacancy_line_title(v)}» {label}.\n\n{text}",
        vacancy_edit_kb(vid, new_val),
    )


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
    await _edit_or_answer(
        query,
        f"🗑 <b>«{_vacancy_line_title(v)}»</b> o'chirilsinmi?",
        vacancy_delete_confirm_kb(vid),
    )


@router.callback_query(F.data.startswith("advdel_ok:"), AdminFilter())
async def adm_ve_delete(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    try:
        vid = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        return
    v = await Vacancy.get_or_none(vid)
    title = _vacancy_line_title(v) if v else str(vid)
    await Vacancy.delete(vid)

    r = await db.execute(select(Vacancy).order_by(Vacancy.sort_order, Vacancy.id))
    vacs = list(r.scalars().all())
    list_text = "💼 <b>Vakansiyalar:</b>" if vacs else "📭 Hozircha vakansiya yo'q."
    await _edit_or_answer(query, f"✅ «{title}» o'chirildi.\n\n{list_text}", vacancy_admin_list_kb(vacs))


@router.callback_query(F.data.startswith("admback:"), AdminFilter())
async def admin_back(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    data = await state.get_data()
    await _delete_msg(query.bot, query.message.chat.id, data.get("prompt_msg_id"))
    await state.clear()

    raw = query.data or ""
    if raw == "admback:admin":
        n = await _user_count()
        await _edit_or_answer(query, _panel_text(n), admin_main_kb(await _admin_lang(query.from_user.id if query.from_user else None)))
        return
    if raw == "admback:vac_list":
        r = await db.execute(select(Vacancy).order_by(Vacancy.sort_order, Vacancy.id))
        vacs = list(r.scalars().all())
        text = "💼 <b>Vakansiyalar:</b>" if vacs else "📭 Hozircha vakansiya yo'q."
        await _edit_or_answer(query, text, vacancy_admin_list_kb(vacs))
        return
    if raw.startswith("admback:vac_edit:"):
        try:
            vid = int(raw.split(":", 2)[2])
        except (ValueError, IndexError):
            n = await _user_count()
            await _edit_or_answer(query, _panel_text(n), admin_main_kb(await _admin_lang(query.from_user.id if query.from_user else None)))
            return
        text, is_active = await _vacancy_edit_text(vid)
        await _edit_or_answer(query, text, vacancy_edit_kb(vid, is_active))
        return
    n = await _user_count()
    await _edit_or_answer(query, _panel_text(n), admin_main_kb(await _admin_lang(query.from_user.id if query.from_user else None)))


@router.callback_query(F.data == "admstop", AdminFilter())
async def admin_stop(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer("❌ Bekor")
    data = await state.get_data()
    await _delete_msg(query.bot, query.message.chat.id, data.get("prompt_msg_id"))
    await state.clear()
    n = await _user_count()
    await _edit_or_answer(query, _panel_text(n), admin_main_kb(await _admin_lang(query.from_user.id if query.from_user else None)))


@router.callback_query(F.data == "adm:exit", AdminFilter())
async def adm_exit_to_user_menu(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.clear()
    uid = query.from_user.id if query.from_user else 0
    loc = await get_user_locale(uid)
    lang = norm_lang(loc) if loc else LANG_UZ
    from handlers.user import _main_kb

    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    await query.message.answer(msg(lang, "view_back_main"), reply_markup=_main_kb(lang))
