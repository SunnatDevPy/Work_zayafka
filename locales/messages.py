"""Тексты интерфейса: ru | uz."""

from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

LANG_RU = "ru"
LANG_UZ = "uz"
_VALID = frozenset({LANG_RU, LANG_UZ})


def norm_lang(code: str | None) -> str:
    if code in _VALID:
        return code
    return LANG_UZ


# Ключи сообщений (HTML где помечено в использовании)
_UI: dict[str, dict[str, str]] = {
    LANG_RU: {
        "pick_lang": "🌐 <b>Выберите язык</b>\n\n🇷🇺 Русский · 🇺🇿 Oʻzbekcha",
        "lang_saved": "✅ Язык: русский",
        "start": (
            "👋 <b>Добро пожаловать!</b>\n\n"
            "Здесь можно <b>оставить заявку</b> на работу или "
            "<b>посмотреть вакансии</b>.\n\n"
            "Выберите раздел ниже 👇"
        ),
        "view_empty": "📭 Активных вакансий пока нет. Загляните позже.",
        "view_header": "🔍 <b>Доступные вакансии:</b>\n\nВыберите для подробностей 👇",
        "view_back_main": "🏠 Вы в главном меню.\nВыберите раздел 👇",
        "vac_na": "⚠️ Вакансия недоступна.",
        "vac_desc_none": "Описание не указано.",
        "vac_card": "💼 <b>{title}</b>\n\n📄 {desc}",
        "apply_empty": "📭 Активных вакансий пока нет. Загляните позже.",
        "apply_pick": "💼 Выберите вакансию:",
        "review_caption": (
            "📄 <b>Ваша заявка готова!</b>\n\n"
            "Проверьте данные.\n"
            "Всё верно?"
        ),
        "review_redo": "🔄 Заявка отменена.\nНажмите «📋 Подать заявку», чтобы начать снова.",
        "answer_stop": "🛑 Заполнение заявки остановлено.",
        "faq_empty": "📭 Раздел FAQ пока пуст.\nАдминистратор скоро заполнит.",
        "faq_list_title": "📋 <b>Частые вопросы</b>\n\nВыберите вопрос 👇",
        "faq_not_found": "⚠️ Вопрос не найден.",
        "btn_apply": "📋 Подать заявку",
        "btn_view": "💼 Вакансии",
        "btn_company": "О компании",
        "btn_services": "Услуги",
        "btn_faq": "📋 Частые вопросы",
        "btn_stop_form": "⛔️ Остановить",
        "inline_cancel": "❌ Отмена",
        "inline_back_main": "🔙 Главное меню",
        "inline_back": "🔙 Назад",
        "inline_apply_vac": "🚀 Откликнуться",
        "review_ok": "✅ Подтвердить",
        "review_redo_btn": "🔄 Заново",
        "faq_back_list": "⬅️ Все вопросы",
        "channel_interview_btn": "📞 Вызов на собеседование",
        "channel_reject": "🗑 Удалить",
        "channel_interview_note": "👇 Нажмите кнопку «Вызов на собеседование», чтобы отправить решение кандидату.",
        "channel_interview_sent": "✅ Кандидату отправлено приглашение на собеседование.",
        "interview_user_msg": (
            "🎉 <b>Отличные новости!</b>\n\n"
            "✅ Ваша заявка успешно прошла отбор.\n"
            "📞 Вы <b>приглашены на собеседование</b>.\n\n"
            "⏳ В ближайшее время с вами свяжется HR-менеджер,\n"
            "чтобы согласовать удобные дату и время.\n\n"
            "💙 Спасибо за отклик!"
        ),
        "company_info": (
            "🏢 <b>О компании</b>\n\n"
            "Мы развиваем digital-проекты и медиа-направления, где ценим системность, "
            "креатив и быстрый рост сотрудников."
        ),
        "services_dev": "🛠 Раздел «Услуги» в разработке.",
        "hr_pd_text": (
            "🔐 Перед откликом нужно согласие на обработку персональных данных.\n\n"
            "Нажимая кнопку ниже, вы подтверждаете согласие на обработку данных для подбора персонала."
        ),
        "hr_pd_agree_btn": "Согласен",
        "hr_photo_first_q": (
            "📸 <b>Сначала отправьте вашу фотографию</b> — она будет в начале PDF-заявки.\n"
            "Затем ответьте на вопросы анкеты."
        ),
        "hr_use_inline_hint": "👇 Для этого вопроса выберите вариант кнопкой ниже.",
        "pdf_reply_title": "Отклик",
        "pdf_photo_caption": "Фотография кандидата",
        "pdf_col_field": "Поле",
        "pdf_col_value": "Значение",
        "hr_name_q": "✨ Отлично! Давай знакомиться. Напиши свое Имя и Фамилию.",
        "hr_phone_q": "📞 Поделись номером телефона для связи.",
        "hr_phone_btn": "📱 Отправить контакт",
        "hr_city_q": "Из какого ты города? (Нам важно понимать часовой пояс)\nВыбери один из 12 городов кнопкой ниже 👇",
        "hr_emp_q": "🧩 Какой формат занятости ты рассматриваешь?",
        "hr_emp_full": "Полная занятость",
        "hr_emp_part": "Частичная",
        "hr_emp_project": "Проектная",
        "hr_pay_q": "💸 Как тебе комфортнее выстроить формат оплаты?",
        "hr_pay_fixed": "Фиксированная оплата",
        "hr_pay_scenario": "Оплата за сценарий",
        "hr_pay_salary": "Фикс. оклад в месяц",
        "hr_pay_piece": "Сдельно (за 1 сценарий)",
        "hr_income_q": (
            "💰 Напиши свои финансовые ожидания в цифрах исходя из выбранного формата оплаты.\n\n"
            "<i>Пример: 2 000 000 сум</i>"
        ),
        "hr_resume_q": "📄 Пришли ссылку на свое резюме (Google Docs, hh.ru) или загрузи файл (PDF/Word).",
        "hr_portfolio_q": "🎬 А теперь самое главное для сценариста — портфолио! Пришли ссылку на твои лучшие работы.",
        "hr_photo_q": "📸 И последнее: отправь, пожалуйста, свою фотографию.",
        "hr_test_q": (
            "Супер, данные получили! Последний шаг — небольшое тестовое задание.\n"
            "Оно поможет нам понять твой стиль, а тебе — наши задачи.\n\n"
            "Ссылка на тестовое: {url}"
        ),
        "hr_test_not_set": "⚠️ Для этой вакансии тестовое задание пока не задано. Свяжитесь с администратором.",
        "hr_test_send_ready": "📎 Прикрепить готовое",
        "hr_test_do_later": "⏳ Сделаю позже",
        "hr_test_later_ok": "Договорились! Я напомню тебе о тестовом завтра.",
        "hr_test_waiting": "📎 Отправь готовое тестовое: текст, ссылку или прикрепи файл.",
        "hr_test_reminder": "Напоминаю: пришли сценарий текстом, ссылкой или файлом и нажми «Прикрепить готовое», когда будет готово.",
        "hr_invalid_text": "⚠️ Нужен текстовый ответ. Попробуй еще раз.",
        "hr_invalid_phone": "⚠️ Пришли номер телефона текстом или кнопкой контакта.",
        "hr_invalid_resume": "⚠️ Пришли ссылку на резюме или файл PDF/Word (doc/docx).",
        "hr_invalid_portfolio": "⚠️ Нужна ссылка на портфолио. Отправь URL текстом.",
        "hr_invalid_photo": "⚠️ Отправь, пожалуйста, фото.",
        "hr_invalid_test": "⚠️ Пришли тестовое текстом, ссылкой или файлом.",
        "hr_pdf_error": "⚠️ Не удалось сформировать PDF. Попробуйте ещё раз или нажмите «Остановить».",
        "hr_review_hint": "👇 Под сообщением с PDF нажмите «Подтвердить», чтобы отправить отклик, или «Заново», чтобы заполнить снова.",
        "hr_done_user": (
            "Бинго! 🎉 Твой отклик успешно улетел нашему HR-менеджеру.\n"
            "Мы изучим материалы и вернемся с обратной связью в течение нескольких рабочих дней. Удачи!"
        ),
        "scenario_task_prompt": (
            "🎬 <b>Задание:</b> напиши сценарий (можно в сообщении, ссылкой на документ или файлом).\n\n"
            "✍️ Подойдёт текст, ссылка или вложение.\n"
            "👇 Когда готово — «Прикрепить готовое»; нужно время — «Сделаю позже».\n\n"
            "⛔️ Прервать анкету: кнопка «Остановить» или /cancel"
        ),
    },
    LANG_UZ: {
        "pick_lang": "🌐 <b>Tilni tanlang</b>\n\n🇷🇺 Русский · 🇺🇿 Oʻzbekcha",
        "lang_saved": "✅ Til: o‘zbekcha",
        "start": (
            "👋 <b>Assalomu alaykum!</b>\n\n"
            "Bu yerda ishga <b>ariza</b> qoldirishingiz yoki "
            "<b>vakansiyalar</b> bilan tanishishingiz mumkin.\n\n"
            "Quyidagi tugmalardan birini tanlang 👇"
        ),
        "view_empty": "📭 Hozircha faol vakansiya yo‘q. Keyinroq urinib ko‘ring.",
        "view_header": "🔍 <b>Mavjud vakansiyalar:</b>\n\nBatafsil ko‘rish uchun tanlang 👇",
        "view_back_main": "🏠 Asosiy menyuga qaytdingiz.\nKerakli bo‘limni tanlang 👇",
        "vac_na": "⚠️ Vakansiya mavjud emas.",
        "vac_desc_none": "Tavsif qo'shilmagan.",
        "vac_card": "💼 <b>{title}</b>\n\n📄 {desc}",
        "apply_empty": "📭 Hozircha faol vakansiya yo‘q. Keyinroq urinib ko‘ring.",
        "apply_pick": "💼 Vakansiyani tanlang:",
        "review_caption": (
            "📄 <b>Arizangiz tayyor!</b>\n\n"
            "Ma'lumotlarni tekshirib ko'ring.\n"
            "Hammasi to'g'rimi?"
        ),
        "review_redo": "🔄 Ariza bekor qilindi.\nQaytadan boshlash uchun «📋 Ariza qoldirish» tugmasini bosing.",
        "answer_stop": "🛑 Ariza topshirish to'xtatildi.",
        "faq_empty": "📭 Hozircha FAQ qo'shilmagan.\nAdministrator tez orada to'ldiradi.",
        "faq_list_title": "📋 <b>Tez-tez so'raladigan savollar</b>\n\nQiziqtirgan savolni tanlang 👇",
        "faq_not_found": "⚠️ Savol topilmadi.",
        "btn_apply": "📋 Ariza qoldirish",
        "btn_view": "💼 Vakansiyalar",
        "btn_company": "Kompaniya haqida",
        "btn_services": "Xizmatlar",
        "btn_faq": "📋 Tez-tez so'raladigan savollar",
        "btn_stop_form": "⛔️ To'xtatish",
        "inline_cancel": "❌ Bekor qilish",
        "inline_back_main": "🔙 Asosiy menyu",
        "inline_back": "🔙 Orqaga",
        "inline_apply_vac": "🚀 Ariza berish",
        "review_ok": "✅ Tasdiqlash",
        "review_redo_btn": "🔄 Qaytadan",
        "faq_back_list": "⬅️ Barcha savollar",
        "channel_interview_btn": "📞 Suhbatga chaqirish",
        "channel_reject": "🗑 Rad etish",
        "channel_interview_note": "👇 Nomzodga qarorni yuborish uchun «Suhbatga chaqirish» tugmasini bosing.",
        "channel_interview_sent": "✅ Nomzodga suhbatga taklif yuborildi.",
        "interview_user_msg": (
            "🎉 <b>Ajoyib yangilik!</b>\n\n"
            "✅ Arizangiz saralashdan muvaffaqiyatli o'tdi.\n"
            "📞 Siz <b>suhbatga taklif qilindingiz</b>.\n\n"
            "⏳ Tez orada HR menejer siz bilan bog'lanib,\n"
            "qulay sana va vaqtni kelishib oladi.\n\n"
            "💙 Ariza qoldirganingiz uchun rahmat!"
        ),
        "company_info": (
            "🏢 <b>Kompaniya haqida</b>\n\n"
            "Biz digital yo'nalishda rivojlanayotgan jamoamiz va ijodkor, mas'uliyatli mutaxassislarni qadrlaymiz."
        ),
        "services_dev": "🛠 «Xizmatlar» bo'limi ishlab chiqilmoqda.",
        "hr_pd_text": (
            "🔐 Ariza yuborishdan oldin shaxsiy ma'lumotlarni qayta ishlashga rozilik kerak.\n\n"
            "Quyidagi tugmani bosib, ishga qabul jarayoni uchun ma'lumotlaringizni qayta ishlashga rozilik bildirasiz."
        ),
        "hr_pd_agree_btn": "Roziman",
        "hr_photo_first_q": (
            "📸 <b>Avvalo suratingizni yuboring</b> — u PDF-arizaning boshida bo‘ladi.\n"
            "Keyin savollarga javob berasiz."
        ),
        "hr_use_inline_hint": "👇 Bu savol uchun quyidagi tugmalar orqali tanlang.",
        "pdf_reply_title": "Ariza",
        "pdf_photo_caption": "Nomzod surati",
        "pdf_col_field": "Maydon",
        "pdf_col_value": "Qiymat",
        "hr_name_q": "✨ Ajoyib! Keling, tanishamiz. Ism va familiyangizni yozing.",
        "hr_phone_q": "📞 Bog'lanish uchun telefon raqamingizni yuboring.",
        "hr_phone_btn": "📱 Kontaktni yuborish",
        "hr_city_q": "Qaysi shahardansiz? (Soat mintaqasi muhim)\n12 ta shahardan birini quyidagi tugmalar bilan tanlang 👇",
        "hr_emp_q": "🧩 Qaysi bandlik formatini ko'rib chiqyapsiz?",
        "hr_emp_full": "To‘liq bandlik",
        "hr_emp_part": "Qisman",
        "hr_emp_project": "Loyihaviy",
        "hr_pay_q": "💸 To'lov formatini qanday qulay deb bilasiz?",
        "hr_pay_fixed": "Fiks to‘lov",
        "hr_pay_scenario": "Ssenariy bo‘yicha to‘lov",
        "hr_pay_salary": "Oylik fiks maosh",
        "hr_pay_piece": "Ssenariy bo'yicha (dona)",
        "hr_income_q": (
            "💰 Tanlangan formatga ko'ra moliyaviy kutuvingizni raqamda yozing.\n\n"
            "<i>Misol: 2 000 000 so'm</i>"
        ),
        "hr_resume_q": "📄 Rezyume havolasini yuboring (Google Docs, hh.ru) yoki PDF/Word fayl yuklang.",
        "hr_portfolio_q": "🎬 Ssenarist uchun eng muhimi — portfolio! Eng yaxshi ishlaringiz havolasini yuboring.",
        "hr_photo_q": "📸 Oxirgi qadam: iltimos, o'z rasmingizni yuboring.",
        "hr_test_q": (
            "Zo'r, ma'lumotlar olindi! Oxirgi qadam — kichik test vazifa.\n"
            "U uslubingizni tushunishga yordam beradi.\n\n"
            "Test havolasi: {url}"
        ),
        "hr_test_not_set": "⚠️ Bu vakansiya uchun test vazifa hali kiritilmagan. Administrator bilan bog'laning.",
        "hr_test_send_ready": "📎 Tayyorini yuborish",
        "hr_test_do_later": "⏳ Keyinroq qilaman",
        "hr_test_later_ok": "Kelishdik! Ertaga test vazifa haqida eslataman.",
        "hr_test_waiting": "📎 Tayyor testni yuboring: matn, havola yoki fayl.",
        "hr_test_reminder": "Eslatma: ssenariyni matn, havola yoki fayl bilan yuboring; tayyor bo‘lsa «Tayyorini yuborish» tugmasini bosing.",
        "hr_invalid_text": "⚠️ Matnli javob yuboring.",
        "hr_invalid_phone": "⚠️ Telefonni matn yoki kontakt tugmasi orqali yuboring.",
        "hr_invalid_resume": "⚠️ Rezyume havolasi yoki PDF/Word (doc/docx) fayl yuboring.",
        "hr_invalid_portfolio": "⚠️ Portfolio havolasini URL ko'rinishida yuboring.",
        "hr_invalid_photo": "⚠️ Iltimos, foto yuboring.",
        "hr_invalid_test": "⚠️ Test javobini matn, havola yoki fayl sifatida yuboring.",
        "hr_pdf_error": "⚠️ PDF yaratib bo'lmadi. Qayta urinib ko'ring yoki «To'xtatish» tugmasini bosing.",
        "hr_review_hint": "👇 PDF ostidagi «Tasdiqlash» tugmasi bilan yuboring yoki «Qaytadan» bilan qayta to'ldiring.",
        "hr_done_user": (
            "Bingo! 🎉 Arizangiz HR menejerga yuborildi.\n"
            "Materiallarni ko'rib chiqib, bir necha ish kunida javob beramiz. Omad!"
        ),
        "scenario_task_prompt": (
            "🎬 <b>Vazifa:</b> ssenariy yozing (xabar, hujjat havolasi yoki fayl bilan).\n\n"
            "✍️ Matn, havola yoki fayl mos keladi.\n"
            "👇 Tayyor bo‘lsa — «Tayyorini yuborish»; vaqt kerak — «Keyinroq qilaman».\n\n"
            "⛔️ To‘xtatish: «To'xtatish» tugmasi yoki /cancel"
        ),
    },
}


def msg(lang: str, key: str, **kwargs) -> str:
    lg = norm_lang(lang)
    text = _UI[lg].get(key) or _UI[LANG_UZ][key]
    return text.format(**kwargs) if kwargs else text


def pick_language_prompt() -> str:
    """Нейтральное приветствие до выбора языка (дублирует оба языка в одном сообщении)."""
    return (
        "🌐 <b>Tilni tanlang / Выберите язык</b>\n\n"
        "🇺🇿 Oʻzbekcha  ·  🇷🇺 Русский"
    )


def main_menu_kb(lang: str) -> ReplyKeyboardMarkup:
    lg = norm_lang(lang)
    d = _UI[lg]
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=d["btn_company"]), KeyboardButton(text=d["btn_services"])],
            [KeyboardButton(text=d["btn_view"], style="success")],
        ],
        resize_keyboard=True,
    )


def all_labels(key: str) -> list[str]:
    """Для F.text.in_(...) — оба варианта кнопки."""
    return [_UI[LANG_RU][key], _UI[LANG_UZ][key]]
