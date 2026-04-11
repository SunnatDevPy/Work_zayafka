"""Фиксированная анкета (19 вопросов после фото). Вопросы не хранятся в БД."""

from __future__ import annotations

from typing import Literal, TypedDict


class SurveyItem(TypedDict):
    kind: Literal["text", "phone", "city", "employment", "payment"]
    pdf_ru: str
    pdf_uz: str
    ask_ru: str
    ask_uz: str


SURVEY_ITEMS: list[SurveyItem] = [
    {
        "kind": "text",
        "pdf_ru": "Имя и фамилия",
        "pdf_uz": "Ism va familiya",
        "ask_ru": (
            "🌿 <b>Вопрос 1 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "👋 <b>Знакомство</b>\n\n"
            "Как к вам обращаться? Укажите <b>имя и фамилию</b>.\n\n"
            "✏️ Напишите ответ одним сообщением ↓"
        ),
        "ask_uz": (
            "🌿 <b>1-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "👋 <b>Tanishuv</b>\n\n"
            "<b>Ism va familiyangizni</b> yozing.\n\n"
            "✏️ Javobni bitta xabar bilan yuboring ↓"
        ),
    },
    {
        "kind": "phone",
        "pdf_ru": "Контактный телефон",
        "pdf_uz": "Aloqa telefoni",
        "ask_ru": (
            "📱 <b>Вопрос 2 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "☎️ <b>Связь</b>\n\n"
            "Оставьте <b>номер телефона</b> — текстом или кнопкой «Отправить контакт».\n\n"
            "💬 Мы свяжемся, когда будет удобно."
        ),
        "ask_uz": (
            "📱 <b>2-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "☎️ <b>Aloqa</b>\n\n"
            "<b>Telefon raqamingizni</b> matn yoki «Kontaktni yuborish» tugmasi bilan yuboring.\n\n"
            "💬 Qulay paytda bog‘lanamiz."
        ),
    },
    {
        "kind": "city",
        "pdf_ru": "Город",
        "pdf_uz": "Shahar",
        "ask_ru": (
            "📍 <b>Вопрос 3 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "🏙️ <b>Ваш город</b>\n\n"
            "Где вы сейчас находитесь? Выберите город на <b>клавиатуре ниже</b>."
        ),
        "ask_uz": (
            "📍 <b>3-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "🏙️ <b>Shaharingiz</b>\n\n"
            "Hozir qayerdasiz? <b>Quyidagi tugmalar</b> orqali tanlang."
        ),
    },
    {
        "kind": "employment",
        "pdf_ru": "Формат занятости",
        "pdf_uz": "Bandlik formati",
        "ask_ru": (
            "🧩 <b>Вопрос 4 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "⏰ <b>Занятость</b>\n\n"
            "Какой формат вам ближе?\n"
            "<i>Полная · частичная · проектная</i>\n\n"
            "👇 Выберите вариант на кнопках"
        ),
        "ask_uz": (
            "🧩 <b>4-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "⏰ <b>Bandlik</b>\n\n"
            "Qaysi format sizga mos?\n"
            "<i>To‘liq · qisman · loyihaviy</i>\n\n"
            "👇 Tugmalar orqali tanlang"
        ),
    },
    {
        "kind": "payment",
        "pdf_ru": "Формат оплаты",
        "pdf_uz": "To‘lov formati",
        "ask_ru": (
            "💳 <b>Вопрос 5 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "💰 <b>Оплата</b>\n\n"
            "Что вам комфортнее?\n"
            "<i>Фиксированная оплата · оплата за сценарий</i>\n\n"
            "👇 Нажмите подходящую кнопку"
        ),
        "ask_uz": (
            "💳 <b>5-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "💰 <b>To‘lov</b>\n\n"
            "Sizga nima qulay?\n"
            "<i>Fiks to‘lov · ssenariy bo‘yicha</i>\n\n"
            "👇 Mos tugmani bosing"
        ),
    },
    {
        "kind": "text",
        "pdf_ru": "Финансовые ожидания",
        "pdf_uz": "Moliyaviy kutishlar",
        "ask_ru": (
            "📊 <b>Вопрос 6 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "💵 <b>Ожидания</b>\n\n"
            "Опишите ваши <b>финансовые ожидания</b> в цифрах (с учётом выбранного формата оплаты).\n\n"
            "✨ Пример: <i>2 000 000 сум</i>\n\n"
            "✏️ Ответ текстом ↓"
        ),
        "ask_uz": (
            "📊 <b>6-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "💵 <b>Kutilmalar</b>\n\n"
            "Tanlangan to‘lov formatiga mos <b>moliyaviy kutishingizni</b> raqamda yozing.\n\n"
            "✨ Misol: <i>2 000 000 so‘m</i>\n\n"
            "✏️ Matn bilan javob ↓"
        ),
    },
    {
        "kind": "text",
        "pdf_ru": "Опыт написания сценариев",
        "pdf_uz": "Ssenariy yozish tajribasi",
        "ask_ru": (
            "🎬 <b>Вопрос 7 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "✍️ <b>Опыт сценариста</b>\n\n"
            "Был ли опыт написания сценариев? Если да — расскажите, в каких <b>форматах и платформах</b> работали.\n\n"
            "🎞️ Чем богаче детали, тем лучше мы поймём ваш стиль.\n\n"
            "✏️ Ваш ответ ↓"
        ),
        "ask_uz": (
            "🎬 <b>7-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "✍️ <b>Ssenariy tajribasi</b>\n\n"
            "Ssenariy yozganmisiz? Agar ha — qaysi <b>format va platformalarda</b> ishlagansiz?\n\n"
            "🎞️ Batafsilroq — yaxshiroq tushunamiz.\n\n"
            "✏️ Javobingiz ↓"
        ),
    },
    {
        "kind": "text",
        "pdf_ru": "Эффективное короткое видео (Reels)",
        "pdf_uz": "Qisqa video (Reels) samaradorligi",
        "ask_ru": (
            "🎥 <b>Вопрос 8 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "✨ <b>Магия Reels</b>\n\n"
            "Что делает короткое видео <b>эффективным и вовлекающим</b>? Поделитесь своим взглядом.\n\n"
            "🔥 Можно примеры, которые вам запомнились.\n\n"
            "✏️ Пишите свободно ↓"
        ),
        "ask_uz": (
            "🎥 <b>8-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "✨ <b>Reels miyasi</b>\n\n"
            "Qisqa video nima uchun <b>samarali va qiziqarli</b> bo‘ladi? O‘z fikringizni yozing.\n\n"
            "🔥 Esingizda qolgan namunalar — xush keladi.\n\n"
            "✏️ Erkin yozing ↓"
        ),
    },
    {
        "kind": "text",
        "pdf_ru": "Первые 3 секунды видео",
        "pdf_uz": "Videoning dastlabki 3 soniyasi",
        "ask_ru": (
            "⚡ <b>Вопрос 9 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "👀 <b>Первые 3 секунды</b>\n\n"
            "Как удержать внимание зрителя в самом начале ролика?\n\n"
            "🎯 Что должно произойти в этот момент?\n\n"
            "✏️ Ваш ответ ↓"
        ),
        "ask_uz": (
            "⚡ <b>9-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "👀 <b>Dastlabki 3 soniya</b>\n\n"
            "Tomoshabin e’tiborini boshida qanday ushlab turish mumkin?\n\n"
            "🎯 Shu paytda nima bo‘lishi kerak?\n\n"
            "✏️ Javobingiz ↓"
        ),
    },
    {
        "kind": "text",
        "pdf_ru": "Идея Reels (напитки / доставка)",
        "pdf_uz": "Reels g‘oyasi (ichimlik / yetkazib berish)",
        "ask_ru": (
            "🥤 <b>Вопрос 10 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "🛵 <b>Идея под заказ</b>\n\n"
            "Предложите <b>одну идею Reels</b> для бизнеса: напитки или доставка еды.\n"
            "<i>Например: Uzum Tezkor, Яндекс Еда…</i>\n\n"
            "💡 Коротко суть + зачем зрителю смотреть.\n\n"
            "✏️ Ваш вариант ↓"
        ),
        "ask_uz": (
            "🥤 <b>10-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "🛵 <b>G‘oya buyurtmasi</b>\n\n"
            "Ichimlik yoki ovqat yetkazib berish uchun <b>bitta Reels g‘oyasi</b> taklif qiling.\n"
            "<i>Masalan: Uzum Tezkor, Yandex Eda…</i>\n\n"
            "💡 Qisqa: nima va nima uchun qiziqarli.\n\n"
            "✏️ Sizning variant ↓"
        ),
    },
    {
        "kind": "text",
        "pdf_ru": "Продажи через видео без давления",
        "pdf_uz": "Video orqali bosimsiz sotish",
        "ask_ru": (
            "🤝 <b>Вопрос 11 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "🌊 <b>Мягкие продажи</b>\n\n"
            "Как <b>продавать через видео</b>, не давя на аудиторию?\n\n"
            "🎨 Расскажите о приёмах, которые вам нравятся.\n\n"
            "✏️ Ваш ответ ↓"
        ),
        "ask_uz": (
            "🤝 <b>11-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "🌊 <b>Yumshoq sotuv</b>\n\n"
            "Auditoriyaga bosim qilmasdan <b>video orqali qanday sotish</b> mumkin?\n\n"
            "🎨 Yoqtirgan usullaringizni yozing.\n\n"
            "✏️ Javobingiz ↓"
        ),
    },
    {
        "kind": "text",
        "pdf_ru": "Краткий сценарий (до 30 сек)",
        "pdf_uz": "Qisqa ssenariy (30 soniyagacha)",
        "ask_ru": (
            "📝 <b>Вопрос 12 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "🎞️ <b>Мини-сценарий</b>\n\n"
            "Напишите <b>краткий сценарий до 30 секунд</b> на тему:\n"
            "«Почему стоит выбрать нашу компанию».\n\n"
            "🌟 Можно кадры, реплики, музыкальное настроение — как удобно.\n\n"
            "✏️ Текстом ниже ↓"
        ),
        "ask_uz": (
            "📝 <b>12-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "🎞️ <b>Mini-ssenariy</b>\n\n"
            "<b>30 soniyagacha</b> qisqa ssenariy yozing:\n"
            "«Nima uchun kompaniyamizni tanlash kerak».\n\n"
            "🌟 Kadr, replika, kayfiyat — ixtiyoriy.\n\n"
            "✏️ Matn bilan ↓"
        ),
    },
    {
        "kind": "text",
        "pdf_ru": "Источники идей для контента",
        "pdf_uz": "Kontent g‘oyalari manbalari",
        "ask_ru": (
            "🔮 <b>Вопрос 13 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "💡 <b>Откуда идеи?</b>\n\n"
            "Где вы обычно находите <b>идеи для контента</b>?\n\n"
            "🌍 Подкасты, ленты, книги, жизнь — всё считается.\n\n"
            "✏️ Поделитесь ↓"
        ),
        "ask_uz": (
            "🔮 <b>13-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "💡 <b>G‘oya qayerdan?</b>\n\n"
            "Odatda <b>kontent g‘oyalari</b>ni qayerdan olasiz?\n\n"
            "🌍 Podkast, ijtimoiy tarmoq, kitob, hayot — hammasi mos.\n\n"
            "✏️ Yozing ↓"
        ),
    },
    {
        "kind": "text",
        "pdf_ru": "Три автора / блогера",
        "pdf_uz": "Uchta bloger yoki muallif",
        "ask_ru": (
            "⭐ <b>Вопрос 14 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "👥 <b>Ваши ориентиры</b>\n\n"
            "Назовите <b>3 блогеров или авторов</b>, чей контент кажется вам сильным, и коротко — почему.\n\n"
            "✨ Нам важен ваш вкус.\n\n"
            "✏️ Список и комментарии ↓"
        ),
        "ask_uz": (
            "⭐ <b>14-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "👥 <b>O‘qituvchilaringiz</b>\n\n"
            "<b>3 nafar bloger yoki muallif</b> — kontenti kuchli deb bilasiz; qisqacha sabab.\n\n"
            "✨ Sizning didingiz muhim.\n\n"
            "✏️ Ro‘yxat va izoh ↓"
        ),
    },
    {
        "kind": "text",
        "pdf_ru": "Задание: салон красоты, 2 сценария",
        "pdf_uz": "Vazifa: go‘zallik saloni, 2 ssenariy",
        "ask_ru": (
            "💇 <b>Вопрос 15 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "✨ <b>Кейс: салон красоты</b>\n\n"
            "Клиент — салон красоты. Придумайте <b>2 сценария Reels</b>:\n"
            "• один <b>информационный</b>\n"
            "• один <b>продающий</b>\n\n"
            "🪄 Покажите разные углы.\n\n"
            "✏️ Оба сценария в одном сообщении ↓"
        ),
        "ask_uz": (
            "💇 <b>15-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "✨ <b>Keyc: go‘zallik saloni</b>\n\n"
            "Mijoz — go‘zallik saloni. <b>2 ta Reels ssenariysi</b>:\n"
            "• bittasi <b>ma’lumotnoma</b>\n"
            "• bittasi <b>sotuvga yo‘naltirilgan</b>\n\n"
            "🪄 Har xil yondashuv ko‘rsating.\n\n"
            "✏️ Ikkalasini bitta xabarda ↓"
        ),
    },
    {
        "kind": "text",
        "pdf_ru": "Сценариев в день",
        "pdf_uz": "Kuniga ssenariylar soni",
        "ask_ru": (
            "📅 <b>Вопрос 16 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "✍️ <b>Темп работы</b>\n\n"
            "Сколько <b>сценариев в день</b> вы готовы писать при полной загрузке?\n\n"
            "☕ Реальная цифра — лучше идеала.\n\n"
            "✏️ Напишите ↓"
        ),
        "ask_uz": (
            "📅 <b>16-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "✍️ <b>Ish tempi</b>\n\n"
            "To‘liq yuk ostida <b>kuniga nechta ssenariy</b> yozishga tayyorsiz?\n\n"
            "☕ Haqiqiy raqam — idealdan yaxshi.\n\n"
            "✏️ Yozing ↓"
        ),
    },
    {
        "kind": "text",
        "pdf_ru": "Отношение к правкам и обратной связи",
        "pdf_uz": "Tahrir va fikr-mulohazalarga munosabat",
        "ask_ru": (
            "🔄 <b>Вопрос 17 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "💬 <b>Обратная связь</b>\n\n"
            "Как вы относитесь к <b>правкам, критике и фидбеку</b> по работе?\n\n"
            "🌱 Честно — так мы быстрее синхронизируемся.\n\n"
            "✏️ Ваш ответ ↓"
        ),
        "ask_uz": (
            "🔄 <b>17-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "💬 <b>Feedback</b>\n\n"
            "Ish bo‘yicha <b>tahrir, tanqid va fikr-mulohazalar</b>ga qanday qaraysiz?\n\n"
            "🌱 Halol javob — tezroq bir xil yo‘nalishda ishlaymiz.\n\n"
            "✏️ Javobingiz ↓"
        ),
    },
    {
        "kind": "text",
        "pdf_ru": "Интерес к компании BMP",
        "pdf_uz": "BMP kompaniyasiga qiziqish",
        "ask_ru": (
            "🏢 <b>Вопрос 18 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "💙 <b>Про BMP</b>\n\n"
            "Почему вам интересно работать именно в компании <b>BMP</b>?\n\n"
            "🎯 Что откликается лично вам?\n\n"
            "✏️ Расскажите ↓"
        ),
        "ask_uz": (
            "🏢 <b>18-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "💙 <b>BMP haqida</b>\n\n"
            "Nima uchun aynan <b>BMP</b>da ishlashni xohlaysiz?\n\n"
            "🎯 Sizga nima tegishli?\n\n"
            "✏️ Yozing ↓"
        ),
    },
    {
        "kind": "text",
        "pdf_ru": "Почему мы должны выбрать вас",
        "pdf_uz": "Nima uchun aynan sizni tanlashimiz kerak",
        "ask_ru": (
            "🚀 <b>Вопрос 19 · из 19</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "🌟 <b>Финишная прямая</b>\n\n"
            "Почему, на ваш взгляд, мы должны выбрать <b>именно вас</b>?\n\n"
            "✨ Смело: сильные стороны, кейсы, энергия — всё уместно.\n\n"
            "✏️ Последний ответ анкеты ↓"
        ),
        "ask_uz": (
            "🚀 <b>19-savol · 19 dan</b>\n"
            "╍╍╍╍╍╍╍╍╍╍╍╍╍╍\n\n"
            "🌟 <b>Oxirgi to‘g‘ri chiziq</b>\n\n"
            "Sizningcha, nima uchun <b>aynan sizni</b> tanlashimiz kerak?\n\n"
            "✨ Kuchli tomonlar, tajriba, energiya — hammasi joyida.\n\n"
            "✏️ So‘nggi javob ↓"
        ),
    },
]


def survey_ask_html(item: SurveyItem, lang: str) -> str:
    from locales.messages import LANG_RU, norm_lang

    lg = norm_lang(lang)
    return item["ask_ru"] if lg == LANG_RU else item["ask_uz"]


def survey_pdf_label(item: SurveyItem, lang: str) -> str:
    from locales.messages import LANG_RU, norm_lang

    lg = norm_lang(lang)
    return item["pdf_ru"] if lg == LANG_RU else item["pdf_uz"]
