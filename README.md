<div align="center">

# 🤖 Work Zayafka Bot

**Telegram HR-bot** — приём заявок от кандидатов, управление вакансиями, FAQ и AI-ассистент

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-009688?logo=telegram&logoColor=white)](https://aiogram.dev)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?logo=databricks&logoColor=white)](https://sqlalchemy.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-316192?logo=postgresql&logoColor=white)](https://postgresql.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai&logoColor=white)](https://openai.com)

</div>

---

## 📌 О проекте

**Work Zayafka Bot** — это полноценная HR-платформа в Telegram. Кандидаты заполняют анкету прямо в боте, получают PDF с заявкой и отправляют её на проверку. Администраторы управляют вакансиями, вопросами анкеты и FAQ через удобную inline-панель.

---

## ✨ Возможности

### 👤 Для кандидатов
| Функция | Описание |
|---------|----------|
| 🔍 **Просмотр вакансий** | Список активных вакансий с описанием |
| 📋 **Подача заявки** | Пошаговая анкета с текстовыми ответами и фото |
| 📄 **PDF заявка** | Автоматически генерируется красивый PDF |
| ✅ **Подтверждение** | Проверить PDF перед отправкой или начать заново |
| 📋 **FAQ** | Быстрые ответы на частые вопросы |
| 🤖 **AI-ассистент** | ChatGPT отвечает на вопросы о компании и вакансиях |

### 🛠 Для администраторов
| Функция | Описание |
|---------|----------|
| 💼 **Вакансии** | Добавить / редактировать название, описание, статус, удалить |
| ❓ **Вопросы анкеты** | Настроить вопросы (текст или фото) под каждую вакансию |
| 📋 **FAQ** | Управление часто задаваемыми вопросами |
| 📢 **Рассылка** | Отправить сообщение всем пользователям |
| ✅ **Обработка заявок** | Принять заявку → отправить кандидату домашнее задание |

---

## 🏗 Структура проекта

```
Zayafka_bot/
├── handlers/
│   ├── admin.py          # Админ-панель (вакансии, вопросы, FAQ, рассылка)
│   ├── ai_chat.py        # AI-ассистент (ChatGPT)
│   ├── channel_review.py # Обработка заявок в канале/группе
│   ├── faq.py            # FAQ для пользователей
│   └── user.py           # Основной флоу пользователя
├── keyboards/
│   └── inline.py         # Все inline-клавиатуры
├── models/
│   ├── bot_user.py       # Модель пользователя (для рассылки)
│   ├── database.py       # Async SQLAlchemy сессия и базовые классы
│   ├── faq.py            # Модель FAQ
│   ├── question.py       # Модель вопроса анкеты
│   └── vacancy.py        # Модель вакансии
├── services/
│   ├── ai.py             # OpenAI интеграция
│   └── pdf.py            # Генерация PDF (reportlab)
├── utils/
│   └── filters.py        # AdminFilter
├── config.py             # Конфигурация из .env
├── main.py               # Точка входа
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Быстрый старт

### 1. Клонировать репозиторий
```bash
git clone https://github.com/SunnatDevPy/Work_zayafka.git
cd Work_zayafka
```

### 2. Создать виртуальное окружение
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Установить зависимости
```bash
pip install -r requirements.txt
```

### 4. Настроить переменные окружения
```bash
cp .env.example .env
```
Открыть `.env` и заполнить все значения (см. раздел [Конфигурация](#⚙️-конфигурация)).

### 5. Создать базу данных PostgreSQL
```sql
CREATE DATABASE zayafka_db;
```
Таблицы создаются автоматически при первом запуске.

### 6. Запустить бота
```bash
python main.py
```

---

## ⚙️ Конфигурация

| Переменная | Обязательная | Описание |
|------------|:---:|---------|
| `BOT_TOKEN` | ✅ | Токен от [@BotFather](https://t.me/BotFather) |
| `ADMIN` | ✅ | Telegram ID главного администратора |
| `ANOTHER_ADMIN` | — | Дополнительный администратор |
| `DB_USER` | ✅ | Пользователь PostgreSQL |
| `DB_PASS` | ✅ | Пароль PostgreSQL |
| `DB_HOST` | — | Хост БД (по умолчанию `localhost`) |
| `DB_PORT` | — | Порт БД (по умолчанию `5432`) |
| `DB_NAME` | ✅ | Название базы данных |
| `GROUP_OR_CHANNEL_ID` | — | ID канала/группы куда приходят заявки |
| `OPENAI_API_KEY` | — | API ключ OpenAI для AI-ассистента |
| `OPENAI_MODEL` | — | Модель GPT (по умолчанию `gpt-4o-mini`) |
| `AI_SYSTEM_PROMPT` | — | Системный промт AI (переопределяет дефолтный) |

---

## 🤖 Флоу пользователя

```
/start
  └── Главное меню
        ├── 🔍 Vakansiyalarni ko'rish
        │     └── Список вакансий → описание → Подать заявку
        ├── 📋 Ariza qoldirish
        │     └── Выбор вакансии → Анкета (вопросы) → PDF
        │           └── [✅ Tasdiqlash] → Отправить в канал
        │           └── [🔄 Qaytadan]  → Начать заново
        ├── 📋 Tez-tez so'raladigan savollar
        │     └── Список FAQ → Вопрос + Ответ
        └── 🤖 AI yordamchi
              └── Чат с ChatGPT о компании и вакансиях
```

---

## 🛠 Флоу администратора

```
/admin
  └── Admin panel
        ├── 💼 Vakansiyalar
        │     ├── Добавить вакансию
        │     └── Нажать вакансию → Редактировать / Удалить
        ├── ❓ Savollar
        │     └── Выбрать вакансию → Добавить / Редактировать вопросы
        ├── 📋 FAQ boshqaruvi
        │     ├── Добавить FAQ (вопрос + ответ)
        │     └── Нажать FAQ → Редактировать / Удалить
        └── 📢 Reklama
              └── Отправить рассылку всем пользователям
```

---

## 📦 Зависимости

| Пакет | Версия | Назначение |
|-------|--------|-----------|
| `aiogram` | `^3.13` | Telegram Bot framework |
| `sqlalchemy[asyncio]` | `^2.0` | ORM для PostgreSQL |
| `asyncpg` | `^0.30` | Async PostgreSQL драйвер |
| `python-dotenv` | `^1.0` | Загрузка `.env` |
| `reportlab` | `^4.2` | Генерация PDF |
| `Pillow` | `^11.0` | Обработка изображений |
| `openai` | `^1.30` | ChatGPT API |
| `aiofiles` | `^24.1` | Async файловые операции |

---

## 📄 PDF заявка

Бот автоматически генерирует красивый PDF с:
- 🎨 Тёмно-синей шапкой с именем вакансии и датой
- 🔢 Пронумерованными карточками вопросов с акцентной полосой
- 📷 Фото кандидата (автоматически ресайзится до 2400px)
- 💬 Текстовыми ответами в оформленных блоках
- 📅 Колонтитулом с датой и временем

---

## 🔒 Безопасность

- Секреты хранятся только в `.env` (в репозиторий **не попадает**)
- Все админ-действия защищены `AdminFilter`
- Файл `.env.example` содержит шаблон без реальных данных

---

## 📝 Лицензия

MIT License © 2026 [SunnatDevPy](https://github.com/SunnatDevPy)
