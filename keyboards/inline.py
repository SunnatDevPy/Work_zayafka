from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.vacancy import Vacancy


def vacancies_kb(vacancies: list[Vacancy]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for v in vacancies:
        b.row(InlineKeyboardButton(text=f"💼 {v.title}", callback_data=f"vac:{v.id}"))
    b.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="vac:cancel"))
    return b.as_markup()


def vacancy_view_list_kb(vacancies: list[Vacancy]) -> InlineKeyboardMarkup:
    """Клиентский список вакансий для просмотра."""
    b = InlineKeyboardBuilder()
    for v in vacancies:
        b.row(InlineKeyboardButton(text=f"📋 {v.title}", callback_data=f"vview:{v.id}"))
    b.row(InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="vview:back"))
    return b.as_markup()


def vacancy_view_detail_kb(vacancy_id: int) -> InlineKeyboardMarkup:
    """Детальный просмотр вакансии + кнопка подать заявку."""
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="📝 Ariza qoldirish", callback_data=f"vac:{vacancy_id}"))
    b.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="vview:back"))
    return b.as_markup()


def review_kb() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения PDF перед отправкой в канал."""
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="rev:ok"),
        InlineKeyboardButton(text="🔄 Qaytadan", callback_data="rev:redo"),
    )
    return b.as_markup()


def admin_main_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="💼 Vakansiyalar",       callback_data="adm:vac"))
    b.row(InlineKeyboardButton(text="❓ Savollar",           callback_data="adm:q"))
    b.row(InlineKeyboardButton(text="📋 FAQ boshqaruvi",     callback_data="adm:faq"))
    b.row(InlineKeyboardButton(text="📢 Reklama",            callback_data="adm:bc"))
    return b.as_markup()


# ── FAQ — user side ──────────────────────────────────────────────────

def faq_list_kb(faqs: list) -> InlineKeyboardMarkup:
    """List of FAQ questions for users."""
    b = InlineKeyboardBuilder()
    for f in faqs:
        short = f.question[:55] + "…" if len(f.question) > 55 else f.question
        b.row(InlineKeyboardButton(text=f"❓ {short}", callback_data=f"faq:{f.id}"))
    b.row(InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="faq:close"))
    return b.as_markup()


def faq_detail_kb() -> InlineKeyboardMarkup:
    """Back button shown on a single FAQ answer."""
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="⬅️ Barcha savollar", callback_data="faq:list"))
    return b.as_markup()


# ── FAQ — admin side ─────────────────────────────────────────────────

def admin_faq_list_kb(faqs: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for f in faqs:
        short = f.question[:48] + "…" if len(f.question) > 48 else f.question
        b.row(InlineKeyboardButton(text=f"📝 {short}", callback_data=f"admfe:{f.id}"))
    b.row(InlineKeyboardButton(text="➕ FAQ qo'shish", callback_data="admfa:add"))
    b.row(InlineKeyboardButton(text="⬅️ Orqaga",      callback_data="admfa:back"))
    return b.as_markup()


def faq_edit_kb(faq_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="✏️ Savolni o'zgartirish", callback_data=f"admfq:{faq_id}"))
    b.row(InlineKeyboardButton(text="✏️ Javobni o'zgartirish", callback_data=f"admfa_ans:{faq_id}"))
    b.row(InlineKeyboardButton(text="🗑 O'chirish",            callback_data=f"admfd:{faq_id}"))
    b.row(InlineKeyboardButton(text="⬅️ Orqaga",              callback_data="adm:faq"))
    return b.as_markup()


def faq_delete_confirm_kb(faq_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"admfd_ok:{faq_id}"),
        InlineKeyboardButton(text="❌ Bekor",         callback_data=f"admfe:{faq_id}"),
    )
    return b.as_markup()


def yes_no_kb(prefix: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Ha",    callback_data=f"{prefix}:1"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data=f"{prefix}:0"),
    )
    return b.as_markup()


def question_photo_kb() -> InlineKeyboardMarkup:
    return yes_no_kb("qph")


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="📤 Hammaga yuborish", callback_data="bc:send"),
        InlineKeyboardButton(text="❌ Bekor",            callback_data="bc:cancel"),
    )
    return b.as_markup()


def vacancies_pick_kb(vacancies: list, prefix: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for v in vacancies:
        b.row(InlineKeyboardButton(text=f"📌 {v.title}", callback_data=f"{prefix}:{v.id}"))
    b.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"{prefix}:back"))
    return b.as_markup()


def channel_application_kb(user_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"app:ok:{user_id}"),
        InlineKeyboardButton(text="🗑 Rad etish",    callback_data="app:del"),
    )
    return b.as_markup()


def homework_invite_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="📤 Vazifani yuborish", callback_data="hw:go"))
    return b.as_markup()


def homework_done_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="✅ Tayyor", callback_data="hw:done"))
    return b.as_markup()


def vacancy_admin_list_kb(vacancies: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for v in vacancies:
        mark = "✅" if v.is_active else "⏸"
        b.row(InlineKeyboardButton(text=f"{mark} {v.title}", callback_data=f"admve:{v.id}"))
    b.row(InlineKeyboardButton(text="➕ Vakansiya qo'shish", callback_data="admva:add"))
    return b.as_markup()


def vacancy_edit_kb(vacancy_id: int, is_active: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="✏️ Nomni o'zgartirish",    callback_data=f"advt:{vacancy_id}"))
    b.row(InlineKeyboardButton(text="📝 Tavsifni o'zgartirish", callback_data=f"advd:{vacancy_id}"))
    toggle = "⏸ Faolsizlashtirish" if is_active else "✅ Faollashtirish"
    b.row(InlineKeyboardButton(text=toggle,                     callback_data=f"adva:{vacancy_id}"))
    b.row(InlineKeyboardButton(text="🗑 O'chirish",             callback_data=f"advdel:{vacancy_id}"))
    b.row(InlineKeyboardButton(text="⬅️ Orqaga",               callback_data="adm:vac"))
    return b.as_markup()


def vacancy_delete_confirm_kb(vacancy_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"advdel_ok:{vacancy_id}"),
        InlineKeyboardButton(text="❌ Bekor",         callback_data=f"admve:{vacancy_id}"),
    )
    return b.as_markup()
