from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from locales.messages import LANG_RU, LANG_UZ, norm_lang, msg
from models.vacancy import Vacancy


def language_pick_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru", style="danger"),
        InlineKeyboardButton(text="🇺🇿 O‘zbekcha", callback_data="lang:uz", style="success"),
    )
    return b.as_markup()


def vacancies_kb(vacancies: list[Vacancy], lang: str = LANG_UZ) -> InlineKeyboardMarkup:
    lg = norm_lang(lang)
    b = InlineKeyboardBuilder()
    for v in vacancies:
        if lg == "ru":
            title = (getattr(v, "title_ru", None) or getattr(v, "title_uz", None) or v.title or "").strip()
        else:
            title = (getattr(v, "title_uz", None) or getattr(v, "title_ru", None) or v.title or "").strip()
        b.row(InlineKeyboardButton(text=f"💼 {title}", callback_data=f"vac:{v.id}"))
    b.row(InlineKeyboardButton(text=msg(lg, "inline_cancel"), style="danger",callback_data="vac:cancel"))
    return b.as_markup()


def vacancy_view_list_kb(vacancies: list[Vacancy], lang: str = LANG_UZ) -> InlineKeyboardMarkup:
    lg = norm_lang(lang)
    b = InlineKeyboardBuilder()
    for v in vacancies:
        if lg == "ru":
            title = (getattr(v, "title_ru", None) or getattr(v, "title_uz", None) or v.title or "").strip()
        else:
            title = (getattr(v, "title_uz", None) or getattr(v, "title_ru", None) or v.title or "").strip()
        b.row(InlineKeyboardButton(text=f"📋 {title}", callback_data=f"vview:{v.id}"))
    b.row(InlineKeyboardButton(text=msg(lg, "inline_back_main"), callback_data="vview:back"))
    return b.as_markup()


def vacancy_view_detail_kb(vacancy_id: int, lang: str = LANG_UZ) -> InlineKeyboardMarkup:
    lg = norm_lang(lang)
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(
            text=msg(lg, "inline_apply_vac"),
            callback_data=f"hrapply:{vacancy_id}",
        )
    )
    b.row(InlineKeyboardButton(text=msg(lg, "inline_back"), callback_data="vview:back"))
    return b.as_markup()

def homework_done_kb(lang: str = LANG_UZ) -> InlineKeyboardMarkup:
    lg = norm_lang(lang)
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=msg(lg, "hw_done_btn"), callback_data="hw:done"))
    return b.as_markup()


def hr_pd_consent_kb(vacancy_id: int, lang: str = LANG_UZ) -> InlineKeyboardMarkup:
    lg = norm_lang(lang)
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=msg(lg, "hr_pd_agree_btn"), callback_data=f"hragree:{vacancy_id}"))
    b.row(InlineKeyboardButton(text=msg(lg, "inline_back"), callback_data=f"vview:{vacancy_id}"))
    return b.as_markup()


def hr_employment_kb(lang: str = LANG_UZ) -> InlineKeyboardMarkup:
    lg = norm_lang(lang)
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=msg(lg, "hr_emp_full"), callback_data="hremp:full"),
        InlineKeyboardButton(text=msg(lg, "hr_emp_part"), callback_data="hremp:part"),
    )
    b.row(InlineKeyboardButton(text=msg(lg, "hr_emp_project"), callback_data="hremp:project"))
    return b.as_markup()


def hr_payment_kb(lang: str = LANG_UZ) -> InlineKeyboardMarkup:
    lg = norm_lang(lang)
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=msg(lg, "hr_pay_fixed"), callback_data="hrpay:fixed"),
        InlineKeyboardButton(text=msg(lg, "hr_pay_scenario"), callback_data="hrpay:scenario"),
    )
    return b.as_markup()


# id в callback — латиница; подпись на кнопке — только язык интерфейса (ru | uz).
CITY_ROWS: list[tuple[str, str, str]] = [
    ("Toshkent", "Ташкент", "Toshkent"),
    ("Samarqand", "Самарканд", "Samarqand"),
    ("Buxoro", "Бухара", "Buxoro"),
    ("Andijon", "Андижан", "Andijon"),
    ("Fargona", "Фергана", "Farg‘ona"),
    ("Namangan", "Наманган", "Namangan"),
    ("Nukus", "Нукус", "Nukus"),
    ("Xiva", "Хива", "Xiva"),
    ("Qarshi", "Карши", "Qarshi"),
    ("Termiz", "Термез", "Termiz"),
    ("Jizzax", "Джизак", "Jizzax"),
    ("Navoiy", "Навои", "Navoiy"),
]


def city_label_for_lang(city_id: str, lang: str) -> str:
    lg = norm_lang(lang)
    for cid, ru, uz in CITY_ROWS:
        if cid == city_id:
            return ru if lg == LANG_RU else uz
    return city_id


def city_answer_for_pdf(city_id: str, lang: str) -> str:
    return city_label_for_lang(city_id, lang)


def hr_city_kb(lang: str = LANG_UZ) -> InlineKeyboardMarkup:
    lg = norm_lang(lang)
    b = InlineKeyboardBuilder()
    for i in range(0, len(CITY_ROWS), 2):
        left_id, left_ru, left_uz = CITY_ROWS[i]
        left_lbl = left_ru if lg == LANG_RU else left_uz
        if i + 1 < len(CITY_ROWS):
            right_id, right_ru, right_uz = CITY_ROWS[i + 1]
            right_lbl = right_ru if lg == LANG_RU else right_uz
            b.row(
                InlineKeyboardButton(text=left_lbl, callback_data=f"hrcity:{left_id}"),
                InlineKeyboardButton(text=right_lbl, callback_data=f"hrcity:{right_id}"),
            )
        else:
            b.row(InlineKeyboardButton(text=left_lbl, callback_data=f"hrcity:{left_id}"))
    return b.as_markup()


def hr_test_choice_kb(lang: str = LANG_UZ) -> InlineKeyboardMarkup:
    lg = norm_lang(lang)
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=msg(lg, "hr_test_send_ready"), callback_data="hrtest:send"),
        InlineKeyboardButton(text=msg(lg, "hr_test_do_later"), callback_data="hrtest:later"),
    )
    return b.as_markup()


def hr_review_kb(lang: str = LANG_UZ) -> InlineKeyboardMarkup:
    """Подтверждение HR-отклика перед отправкой в канал (отдельные callback от старой анкеты)."""
    lg = norm_lang(lang)
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=msg(lg, "review_ok"), callback_data="hrrev:ok"),
        InlineKeyboardButton(text=msg(lg, "review_redo_btn"), callback_data="hrrev:redo"),
    )
    return b.as_markup()


def admin_main_kb(lang: str = LANG_UZ) -> InlineKeyboardMarkup:
    del lang
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="💼 Вакансии / Vakansiyalar", callback_data="adm:vac"))
    b.row(InlineKeyboardButton(text="📢 Рассылка / Reklama", callback_data="adm:bc"))
    b.row(InlineKeyboardButton(text="🏠 Меню пользователя / Foydalanuvchi menyusi", callback_data="adm:exit"))
    return b.as_markup()


# ── FAQ — user side ──────────────────────────────────────────────────

def faq_list_kb(faqs: list, lang: str = LANG_UZ) -> InlineKeyboardMarkup:
    lg = norm_lang(lang)
    b = InlineKeyboardBuilder()
    for f in faqs:
        if lg == "ru":
            q = (getattr(f, "question_ru", None) or getattr(f, "question_uz", None) or f.question or "").strip()
        else:
            q = (getattr(f, "question_uz", None) or getattr(f, "question_ru", None) or f.question or "").strip()
        short = q[:55] + "…" if len(q) > 55 else q
        b.row(InlineKeyboardButton(text=f"❓ {short}", callback_data=f"faq:{f.id}"))
    b.row(InlineKeyboardButton(text=msg(lg, "inline_back_main"), callback_data="faq:close"))
    return b.as_markup()


def faq_detail_kb(lang: str = LANG_UZ) -> InlineKeyboardMarkup:
    lg = norm_lang(lang)
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=msg(lg, "faq_back_list"), callback_data="faq:list"))
    return b.as_markup()


# ── FAQ — admin side ─────────────────────────────────────────────────

def admin_faq_list_kb(faqs: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for f in faqs:
        short = f.question[:48] + "…" if len(f.question) > 48 else f.question
        b.row(InlineKeyboardButton(text=f"📝 {short}", callback_data=f"admfe:{f.id}"))
    b.row(InlineKeyboardButton(text="➕ Добавить FAQ / FAQ qo‘shish", callback_data="admfa:add"))
    b.row(InlineKeyboardButton(text="⬅️ Назад / Orqaga", callback_data="admfa:back"))
    return b.as_markup()


def faq_edit_kb(faq_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="✏️ Изменить вопрос / Savolni o‘zgartirish", callback_data=f"admfq:{faq_id}"))
    b.row(InlineKeyboardButton(text="✏️ Изменить ответ / Javobni o‘zgartirish", callback_data=f"admfa_ans:{faq_id}"))
    b.row(InlineKeyboardButton(text="🗑 Удалить / O‘chirish", callback_data=f"admfd:{faq_id}"))
    b.row(InlineKeyboardButton(text="⬅️ Назад / Orqaga", callback_data="adm:faq"))
    return b.as_markup()


def faq_delete_confirm_kb(faq_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Да / Ha, o‘chirish", callback_data=f"admfd_ok:{faq_id}"),
        InlineKeyboardButton(text="❌ Отмена / Bekor", callback_data=f"admfe:{faq_id}"),
    )
    return b.as_markup()


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="📤 Отправить всем / Hammaga yuborish", callback_data="bc:send"),
        InlineKeyboardButton(text="❌ Отмена / Bekor", callback_data="bc:cancel"),
    )
    return b.as_markup()


def channel_application_kb(user_id: int, lang: str = LANG_UZ) -> InlineKeyboardMarkup:
    lg = norm_lang(lang)
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=msg(lg, "channel_interview_btn"),style="success", callback_data=f"app:int:{user_id}"),
        InlineKeyboardButton(text=msg(lg, "channel_reject"),style="danger", callback_data="app:del"),
    )
    return b.as_markup()


def vacancy_admin_list_kb(vacancies: list) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for v in vacancies:
        mark = "✅" if v.is_active else "⏸"
        tr = (getattr(v, "title_ru", None) or v.title or "").strip()
        tu = (getattr(v, "title_uz", None) or v.title or "").strip()
        label = f"{tr} / {tu}" if tr != tu else (tr or tu or "—")
        if len(label) > 50:
            label = label[:47] + "…"
        b.row(InlineKeyboardButton(text=f"{mark} {label}", callback_data=f"admve:{v.id}"))
    b.row(InlineKeyboardButton(text="➕ Добавить вакансию / Vakansiya qo‘shish", callback_data="admva:add"))
    b.row(InlineKeyboardButton(text="⬅️ Назад / Orqaga", callback_data="admback:admin"))
    return b.as_markup()


def vacancy_edit_kb(vacancy_id: int, is_active: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="✏️ Название / Nomni o‘zgartirish", callback_data=f"advt:{vacancy_id}"))
    b.row(InlineKeyboardButton(text="📝 Описание / Tavsifni o‘zgartirish", callback_data=f"advd:{vacancy_id}"))
    toggle = "⏸ Деактивировать / Faolsizlashtirish" if is_active else "✅ Активировать / Faollashtirish"
    b.row(InlineKeyboardButton(text=toggle, callback_data=f"adva:{vacancy_id}"))
    b.row(InlineKeyboardButton(text="🗑 Удалить / O‘chirish", callback_data=f"advdel:{vacancy_id}"))
    b.row(InlineKeyboardButton(text="⬅️ Назад / Orqaga", callback_data="adm:vac"))
    return b.as_markup()


def vacancy_task_edit_kb(vacancy_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🔗 Ссылка/текст / Link-matn qo‘shish", callback_data=f"advtask_text:{vacancy_id}"))
    b.row(InlineKeyboardButton(text="🗑 Удалить тест / Testni o‘chirish", callback_data=f"advtask_clear:{vacancy_id}"))
    b.row(InlineKeyboardButton(text="⬅️ Назад / Orqaga", callback_data=f"admve:{vacancy_id}"))
    return b.as_markup()


def vacancy_delete_confirm_kb(vacancy_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Да / Ha, o‘chirish", callback_data=f"advdel_ok:{vacancy_id}"),
        InlineKeyboardButton(text="❌ Отмена / Bekor", callback_data=f"admve:{vacancy_id}"),
    )
    return b.as_markup()
