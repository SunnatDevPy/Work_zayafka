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
        "vac_no_questions": "⚠️ Для этой вакансии пока нет вопросов. Свяжитесь с администратором.",
        "vac_desc_none": "Описание не указано.",
        "vac_card": "💼 <b>{title}</b>\n\n📄 {desc}",
        "apply_empty": "📭 Активных вакансий пока нет. Загляните позже.",
        "apply_pick": "💼 Выберите вакансию:",
        "form_start": "💼 <b>{title}</b>\n\n📝 Начинаем анкету.",
        "review_caption": (
            "📄 <b>Ваша заявка готова!</b>\n\n"
            "Проверьте данные.\n"
            "Всё верно?"
        ),
        "review_sent": "✅ <b>Заявка отправлена!</b>\n\nСвяжемся с вами в ближайшее время. 🙌",
        "review_redo": "🔄 Заявка отменена.\nНажмите «📋 Подать заявку», чтобы начать снова.",
        "answer_stop": "🛑 Заполнение заявки остановлено.",
        "answer_need_photo": "📷 Для этого вопроса нужно отправить фото (подпись по желанию).",
        "answer_need_text": "✍️ Для этого вопроса нужен только текст (без фото).",
        "answer_photo_or_skip": "📷 Отправьте фото или нажмите «⏭️ Пропустить».",
        "answer_text_only": "✍️ Отправьте текстовый ответ.",
        "form_hint_photo": "📷 Отправьте фото (подпись по желанию) или нажмите «{skip}».",
        "form_hint_text": "✍️ Напишите ответ текстом.",
        "channel_new_apply": "🆕 Новая заявка: {title}\n{label}",
        "faq_empty": "📭 Раздел FAQ пока пуст.\nАдминистратор скоро заполнит.",
        "faq_list_title": "📋 <b>Частые вопросы</b>\n\nВыберите вопрос 👇",
        "faq_not_found": "⚠️ Вопрос не найден.",
        "ai_off": "⚠️ <b>AI-помощник сейчас недоступен.</b>\n\nАдминистратор настроит позже.",
        "ai_welcome": (
            "🤖 <b>AI-помощник</b>\n\n"
            "Отвечу на вопросы о компании, вакансиях и условиях.\n\n"
            "<b>Примеры:</b>\n"
            "• Какие есть вакансии?\n"
            "• Какая зарплата и бонусы?\n"
            "• Что нужно для заявки?\n"
            "• Какой график?\n\n"
            "💬 Напишите вопрос 👇"
        ),
        "ai_exit_done": "👋 Диалог завершён. В любой момент можно вернуться!",
        "ai_text_only": "✍️ Пожалуйста, отправьте только текст.",
        "ai_thinking": "⏳ Готовлю ответ…",
        "ai_error_generic": "⚠️ Ошибка. Попробуйте ещё раз.",
        "hw_press_first": "Сначала нажмите «Отправить задание».",
        "hw_accept": "✅ Принято",
        "hw_thanks": "🎉 Спасибо! Получено материалов: {n}.",
        "hw_cancel": "❌ Приём задания отменён.",
        "hw_use_cancel": "⛔️ Для отмены отправьте /cancel",
        "hw_send_types": "📎 Отправьте текст, фото, документ, аудио или видео.",
        "hw_saved": "✅ Сохранено ({n}). Можно отправить ещё или нажать «Готово».",
        "hw_start_text": (
            "📤 Отправьте выполненное задание: текст, файл, фото или видео.\n"
            "✅ Когда всё готово — нажмите «Готово».\n\n"
            "⛔️ Отмена: /cancel"
        ),
        "btn_apply": "📋 Подать заявку",
        "btn_view": "💼 Вакансии",
        "btn_company": "О компании",
        "btn_services": "Услуги",
        "btn_ai": "🤖 AI-помощник",
        "btn_faq": "📋 Частые вопросы",
        "btn_skip_photo": "⏭️ Пропустить",
        "btn_stop_form": "⛔️ Остановить",
        "btn_ai_exit": "❌ Завершить чат",
        "inline_cancel": "❌ Отмена",
        "inline_back_main": "🔙 Главное меню",
        "inline_back": "🔙 Назад",
        "inline_apply_vac": "🚀 Откликнуться",
        "review_ok": "✅ Подтвердить",
        "review_redo_btn": "🔄 Заново",
        "hw_send_btn": "📤 Отправить задание",
        "hw_done_btn": "✅ Готово",
        "faq_back_list": "⬅️ Все вопросы",
        "channel_accept": "✅ Принять",
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
        "channel_task_sent": "✅ Принято, задание отправлено кандидату.",
        "homework_pdf_caption": "📎 Тестовое задание (PDF).",
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
        "hr_name_q": "✨ Отлично! Давай знакомиться. Напиши свое Имя и Фамилию.",
        "hr_phone_q": "📞 Поделись номером телефона для связи.",
        "hr_phone_btn": "📱 Отправить контакт",
        "hr_city_q": "Из какого ты города? (Нам важно понимать часовой пояс)\nВыбери город кнопкой ниже.",
        "hr_emp_q": "🧩 Какой формат занятости ты рассматриваешь?",
        "hr_emp_full": "Полная (Full-time)",
        "hr_emp_part": "Частичная / Проектная",
        "hr_pay_q": "💸 Как тебе комфортнее выстроить формат оплаты?",
        "hr_pay_salary": "Фикс. оклад в месяц",
        "hr_pay_piece": "Сдельно (за 1 сценарий)",
        "hr_income_q": "💰 Напиши свои финансовые ожидания в цифрах исходя из выбранного формата оплаты.",
        "hr_resume_q": "📄 Пришли ссылку на свое резюме (Google Docs, hh.ru) или загрузи файл (PDF/Word).",
        "hr_portfolio_q": "🎬 А теперь самое главное для сценариста — портфолио! Пришли ссылку на твои лучшие работы.",
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
        "hr_invalid_text": "⚠️ Нужен текстовый ответ. Попробуй еще раз.",
        "hr_invalid_phone": "⚠️ Пришли номер телефона текстом или кнопкой контакта.",
        "hr_invalid_resume": "⚠️ Пришли ссылку на резюме или файл PDF/Word (doc/docx).",
        "hr_invalid_portfolio": "⚠️ Нужна ссылка на портфолио. Отправь URL текстом.",
        "hr_invalid_test": "⚠️ Пришли тестовое текстом, ссылкой или файлом.",
        "hr_done_user": (
            "Бинго! 🎉 Твой отклик успешно улетел нашему HR-менеджеру.\n"
            "Мы изучим материалы и вернемся с обратной связью в течение нескольких рабочих дней. Удачи!"
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
        "vac_no_questions": "⚠️ Bu vakansiya uchun hozircha savollar yo‘q. Administrator bilan bog‘laning.",
        "vac_desc_none": "Tavsif qo'shilmagan.",
        "vac_card": "💼 <b>{title}</b>\n\n📄 {desc}",
        "apply_empty": "📭 Hozircha faol vakansiya yo‘q. Keyinroq urinib ko‘ring.",
        "apply_pick": "💼 Vakansiyani tanlang:",
        "form_start": "💼 <b>{title}</b>\n\n📝 Anketani boshlaymiz.",
        "review_caption": (
            "📄 <b>Arizangiz tayyor!</b>\n\n"
            "Ma'lumotlarni tekshirib ko'ring.\n"
            "Hammasi to'g'rimi?"
        ),
        "review_sent": "✅ <b>Arizangiz yuborildi!</b>\n\nTez orada siz bilan bog'lanamiz. 🙌",
        "review_redo": "🔄 Ariza bekor qilindi.\nQaytadan boshlash uchun «📋 Ariza qoldirish» tugmasini bosing.",
        "answer_stop": "🛑 Ariza topshirish to'xtatildi.",
        "answer_need_photo": "📷 Bu savol uchun rasm yuborishingiz kerak (izoh ixtiyoriy).",
        "answer_need_text": "✍️ Bu savol uchun faqat matn kerak (rasm emas).",
        "answer_photo_or_skip": "📷 Rasm yuboring yoki «⏭️ O'tkazib yuborish» tugmasini bosing.",
        "answer_text_only": "✍️ Matnli javob yuboring.",
        "form_hint_photo": "📷 Rasm yuboring (izoh ixtiyoriy) yoki «{skip}» tugmasini bosing.",
        "form_hint_text": "✍️ Javobni matn bilan yozing.",
        "channel_new_apply": "🆕 Yangi ariza: {title}\n{label}",
        "faq_empty": "📭 Hozircha FAQ qo'shilmagan.\nAdministrator tez orada to'ldiradi.",
        "faq_list_title": "📋 <b>Tez-tez so'raladigan savollar</b>\n\nQiziqtirgan savolni tanlang 👇",
        "faq_not_found": "⚠️ Savol topilmadi.",
        "ai_off": "⚠️ <b>AI yordamchi hozirda ulangan emas.</b>\n\nAdministrator tez orada sozlaydi.",
        "ai_welcome": (
            "🤖 <b>AI Yordamchi</b>\n\n"
            "Kompaniyamiz, vakansiyalar va ish sharoitlari haqida savollaringizga javob beraman.\n\n"
            "<b>Misol savollar:</b>\n"
            "• Qanday vakansiyalar mavjud?\n"
            "• Ish haqi va bonuslar qanday?\n"
            "• Ariza berish uchun nima kerak?\n"
            "• Ish grafigi qanday?\n\n"
            "💬 Savolingizni yozing 👇"
        ),
        "ai_exit_done": "👋 Suhbat tugatildi. Istalgan vaqt qaytishingiz mumkin!",
        "ai_text_only": "✍️ Iltimos, faqat matnli savol yuboring.",
        "ai_thinking": "⏳ Javob tayyorlanmoqda…",
        "ai_error_generic": "⚠️ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
        "hw_press_first": "Avvalo «Vazifani yuborish» tugmasini bosing.",
        "hw_accept": "✅ Qabul qilindi",
        "hw_thanks": "🎉 Rahmat! Qabul qilingan materiallar: {n} ta.",
        "hw_cancel": "❌ Vazifa qabul qilish bekor qilindi.",
        "hw_use_cancel": "⛔️ Bekor qilish uchun /cancel yuboring.",
        "hw_send_types": "📎 Matn, rasm, hujjat, audio yoki video yuboring.",
        "hw_saved": "✅ Saqlandi ({n} ta). Yana yuborishingiz yoki «Tayyor» tugmasini bosing.",
        "hw_start_text": (
            "📤 Bajarilgan vazifani yuboring: matn, fayl, rasm yoki video.\n"
            "✅ Hammasi tayyor bo'lsa — «Tayyor» tugmasini bosing.\n\n"
            "⛔️ Bekor: /cancel"
        ),
        "btn_apply": "📋 Ariza qoldirish",
        "btn_view": "💼 Vakansiyalar",
        "btn_company": "Kompaniya haqida",
        "btn_services": "Xizmatlar",
        "btn_ai": "🤖 AI yordamchi",
        "btn_faq": "📋 Tez-tez so'raladigan savollar",
        "btn_skip_photo": "⏭️ O'tkazib yuborish",
        "btn_stop_form": "⛔️ To'xtatish",
        "btn_ai_exit": "❌ Suhbatni tugatish",
        "inline_cancel": "❌ Bekor qilish",
        "inline_back_main": "🔙 Asosiy menyu",
        "inline_back": "🔙 Orqaga",
        "inline_apply_vac": "🚀 Ariza berish",
        "review_ok": "✅ Tasdiqlash",
        "review_redo_btn": "🔄 Qaytadan",
        "hw_send_btn": "📤 Vazifani yuborish",
        "hw_done_btn": "✅ Tayyor",
        "faq_back_list": "⬅️ Barcha savollar",
        "channel_accept": "✅ Qabul qilish",
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
        "channel_task_sent": "✅ Qabul qilindi — nomzodga vazifa yuborildi.",
        "homework_pdf_caption": "📎 Test vazifasi (PDF).",
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
        "hr_name_q": "✨ Ajoyib! Keling, tanishamiz. Ism va familiyangizni yozing.",
        "hr_phone_q": "📞 Bog'lanish uchun telefon raqamingizni yuboring.",
        "hr_phone_btn": "📱 Kontaktni yuborish",
        "hr_city_q": "Qaysi shahardansiz? (Soat mintaqasi muhim)\nQuyidagi tugmalardan shaharni tanlang.",
        "hr_emp_q": "🧩 Qaysi bandlik formatini ko'rib chiqyapsiz?",
        "hr_emp_full": "To'liq (Full-time)",
        "hr_emp_part": "Qisman / Loyihaviy",
        "hr_pay_q": "💸 To'lov formatini qanday qulay deb bilasiz?",
        "hr_pay_salary": "Oylik fiks maosh",
        "hr_pay_piece": "Ssenariy bo'yicha (dona)",
        "hr_income_q": "💰 Tanlangan formatga ko'ra moliyaviy kutuvingizni raqamda yozing.",
        "hr_resume_q": "📄 Rezyume havolasini yuboring (Google Docs, hh.ru) yoki PDF/Word fayl yuklang.",
        "hr_portfolio_q": "🎬 Ssenarist uchun eng muhimi — portfolio! Eng yaxshi ishlaringiz havolasini yuboring.",
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
        "hr_invalid_text": "⚠️ Matnli javob yuboring.",
        "hr_invalid_phone": "⚠️ Telefonni matn yoki kontakt tugmasi orqali yuboring.",
        "hr_invalid_resume": "⚠️ Rezyume havolasi yoki PDF/Word (doc/docx) fayl yuboring.",
        "hr_invalid_portfolio": "⚠️ Portfolio havolasini URL ko'rinishida yuboring.",
        "hr_invalid_test": "⚠️ Test javobini matn, havola yoki fayl sifatida yuboring.",
        "hr_done_user": (
            "Bingo! 🎉 Arizangiz HR menejerga yuborildi.\n"
            "Materiallarni ko'rib chiqib, bir necha ish kunida javob beramiz. Omad!"
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
            [KeyboardButton(text=d["btn_faq"])],
        ],
        resize_keyboard=True,
    )


def all_labels(key: str) -> list[str]:
    """Для F.text.in_(...) — оба варианта кнопки."""
    return [_UI[LANG_RU][key], _UI[LANG_UZ][key]]
