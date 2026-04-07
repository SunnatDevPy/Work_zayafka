<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1a365d,100:2b6cb0&height=200&section=header&text=Work%20Zayafka%20Bot&fontSize=50&fontColor=ffffff&fontAlignY=38&desc=Telegram%20HR%20Platformasi&descAlignY=58&descSize=20&animation=fadeIn" width="100%"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://aiogram.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-CC0000?style=for-the-badge&logo=databricks&logoColor=white)](https://sqlalchemy.org)

<br/>

> **🚀 Telegram orqali ishga ariza qabul qiluvchi to'liq HR-platforma**
> Vakansiyalar boshqaruvi · PDF ariza · AI yordamchi · FAQ tizimi

<br/>

</div>

---

## 📖 Mundarija

- [🌟 Loyiha haqida](#-loyiha-haqida)
- [✨ Imkoniyatlar](#-imkoniyatlar)
- [🏗 Tuzilma](#-tuzilma)
- [🚀 Ishga tushirish](#-ishga-tushirish)
- [⚙️ Sozlamalar](#️-sozlamalar)
- [🤖 Foydalanuvchi yo'li](#-foydalanuvchi-yoli)
- [🛠 Admin panel](#-admin-panel)
- [📄 PDF ariza](#-pdf-ariza)
- [📦 Kutubxonalar](#-kutubxonalar)

---

## 🌟 Loyiha haqida

**Work Zayafka Bot** — bu Telegram ichida ishlovchi to'liq HR platformasi.

Nomzodlar savolnomani to'ldirib, **PDF ariza** yaratishadi va uni tasdiqlashdan so'ng kanal/guruhga yuborishadi. Adminlar vakansiyalar, savollar, FAQ va reklama xabarlarini qulay **inline-panel** orqali boshqaradi. Bundan tashqari, **ChatGPT** asosida ishluvchi AI yordamchi har qanday savolga javob beradi.

<div align="center">

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│    👤 Foydalanuvchi          🛠 Administrator        │
│    ─────────────────         ─────────────────      │
│    🔍 Vakansiyalarni          💼 Vakansiya           │
│       ko'rish                   qo'shish/tahrirlash  │
│                                                     │
│    📋 Ariza topshirish        ❓ Savol sozlamalari   │
│       (PDF yaratish)                                │
│                                                     │
│    📋 FAQ o'qish              📋 FAQ boshqaruvi      │
│                                                     │
│    🤖 AI yordamchi            📢 Reklama yuborish    │
│       bilan suhbat                                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

</div>

---

## ✨ Imkoniyatlar

### 👤 Foydalanuvchilar uchun

<table>
<tr>
<td width="50%">

**🔍 Vakansiyalarni ko'rish**
Faol vakansiyalar ro'yxati va ularning batafsil tavsifi. Har bir vakansiya uchun savollar sonini ko'rish va ariza berish imkoniyati.

</td>
<td width="50%">

**📋 Ariza topshirish**
Bosqichma-bosqich savolnoma: matnli javoblar va rasm yuklash. Bot jarayonni boshqaradi va siz javoband bo'lasiz.

</td>
</tr>
<tr>
<td>

**📄 Chiroyli PDF ariza**
Barcha javoblar avtomatik ravishda professional ko'rinishdagi PDF hujjatga aylantiriladi. Fotosuratlar ham kiritiladi.

</td>
<td>

**✅ Tasdiqlash bosqichi**
PDF tayyor bo'lgach, foydalanuvchi uni tekshiradi: tasdiqlasa — kanalga yuboriladi, qayta boshlasa — yangi ariza.

</td>
</tr>
<tr>
<td>

**📋 FAQ (Tez-tez so'raladigan savollar)**
Kompaniya va vakansiyalar haqidagi eng ko'p so'raladigan savollarga tezkor javoblar.

</td>
<td>

**🤖 AI Yordamchi**
ChatGPT asosidagi yordamchi kompaniya, vakansiyalar va ish sharoitlari haqida savollarga javob beradi.

</td>
</tr>
</table>

### 🛠 Adminlar uchun

<table>
<tr>
<th>Funksiya</th>
<th>Imkoniyatlar</th>
</tr>
<tr>
<td>💼 <b>Vakansiyalar</b></td>
<td>Qo'shish · Nom tahrirlash · Tavsif yozish · Faol/nofaol qilish · O'chirish</td>
</tr>
<tr>
<td>❓ <b>Savollar</b></td>
<td>Har bir vakansiyaga alohida savollar · Matn yoki rasm talab qilish · Tartibni sozlash</td>
</tr>
<tr>
<td>📋 <b>FAQ</b></td>
<td>Savol va javob qo'shish · Tahrirlash · O'chirish · Tartib sozlash</td>
</tr>
<tr>
<td>📥 <b>Ariza qabul qilish</b></td>
<td>Kanalda PDF ko'rish · Qabul qilish (uy vazifasi yuborish) · Rad etish</td>
</tr>
<tr>
<td>📢 <b>Reklama</b></td>
<td>Barcha foydalanuvchilarga istalgan format (matn/rasm/video) xabar yuborish</td>
</tr>
</table>

---

## 🏗 Tuzilma

```
📁 Work_zayafka/
│
├── 📁 handlers/
│   ├── 🔧 admin.py          ← Admin panel (vakansiya, savol, FAQ, reklama)
│   ├── 🤖 ai_chat.py        ← ChatGPT AI yordamchi
│   ├── 📡 channel_review.py ← Kanalda ariza qabul/rad
│   ├── 📋 faq.py            ← FAQ ko'rish
│   └── 👤 user.py           ← Foydalanuvchi asosiy oqimi
│
├── 📁 keyboards/
│   └── ⌨️ inline.py         ← Barcha inline klaviaturalar
│
├── 📁 models/
│   ├── 🗄 database.py       ← Async SQLAlchemy sessiya va bazaviy klasslar
│   ├── 👤 bot_user.py       ← Foydalanuvchi modeli (reklama uchun)
│   ├── 💼 vacancy.py        ← Vakansiya modeli
│   ├── ❓ question.py       ← Savol modeli
│   └── 📋 faq.py            ← FAQ modeli
│
├── 📁 services/
│   ├── 🤖 ai.py             ← OpenAI integratsiyasi
│   └── 📄 pdf.py            ← PDF yaratish (reportlab)
│
├── 📁 utils/
│   └── 🔒 filters.py        ← AdminFilter
│
├── ⚙️  config.py            ← .env konfiguratsiyasi
├── 🚀 main.py               ← Kirish nuqtasi
├── 📦 requirements.txt
├── 🔐 .env.example
└── 📖 README.md
```

---

## 🚀 Ishga tushirish

### 1️⃣ Repozitoriyani klonlash

```bash
git clone https://github.com/SunnatDevPy/Work_zayafka.git
cd Work_zayafka
```

### 2️⃣ Virtual muhit yaratish

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3️⃣ Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 4️⃣ Muhit o'zgaruvchilarini sozlash

```bash
cp .env.example .env
# .env faylini oching va to'ldiring
```

### 5️⃣ PostgreSQL bazasini yaratish

```sql
CREATE DATABASE zayafka_db;
```

> 💡 Jadvallar bot birinchi marta ishga tushganda **avtomatik** yaratiladi.

### 6️⃣ Botni ishga tushirish

```bash
python main.py
```

---

## ⚙️ Sozlamalar

`.env` faylida quyidagi o'zgaruvchilarni to'ldiring:

<table>
<tr>
<th>O'zgaruvchi</th>
<th align="center">Majburiy</th>
<th>Izoh</th>
</tr>
<tr>
<td><code>BOT_TOKEN</code></td>
<td align="center">✅</td>
<td><a href="https://t.me/BotFather">@BotFather</a> dan olingan token</td>
</tr>
<tr>
<td><code>ADMIN</code></td>
<td align="center">✅</td>
<td>Asosiy admin Telegram ID raqami</td>
</tr>
<tr>
<td><code>ANOTHER_ADMIN</code></td>
<td align="center">—</td>
<td>Qo'shimcha admin (ixtiyoriy)</td>
</tr>
<tr>
<td><code>DB_USER</code></td>
<td align="center">✅</td>
<td>PostgreSQL foydalanuvchisi</td>
</tr>
<tr>
<td><code>DB_PASS</code></td>
<td align="center">✅</td>
<td>PostgreSQL paroli</td>
</tr>
<tr>
<td><code>DB_HOST</code></td>
<td align="center">—</td>
<td>Ma'lumotlar bazasi manzili (standart: <code>localhost</code>)</td>
</tr>
<tr>
<td><code>DB_PORT</code></td>
<td align="center">—</td>
<td>Port (standart: <code>5432</code>)</td>
</tr>
<tr>
<td><code>DB_NAME</code></td>
<td align="center">✅</td>
<td>Ma'lumotlar bazasi nomi</td>
</tr>
<tr>
<td><code>GROUP_OR_CHANNEL_ID</code></td>
<td align="center">—</td>
<td>Arizalar yuboriluvchi kanal/guruh ID si</td>
</tr>
<tr>
<td><code>OPENAI_API_KEY</code></td>
<td align="center">—</td>
<td>AI yordamchi uchun OpenAI API kaliti</td>
</tr>
<tr>
<td><code>OPENAI_MODEL</code></td>
<td align="center">—</td>
<td>GPT modeli (standart: <code>gpt-4o-mini</code>)</td>
</tr>
<tr>
<td><code>AI_SYSTEM_PROMPT</code></td>
<td align="center">—</td>
<td>AI tizim ko'rsatmasi (ixtiyoriy)</td>
</tr>
</table>

---

## 🤖 Foydalanuvchi yo'li

```
/start
  │
  └──► Asosiy menyu
         │
         ├──► 🔍 Vakansiyalarni ko'rish
         │         │
         │         └──► Vakansiya ro'yxati
         │                   │
         │                   └──► Tanlangan vakansiya (tavsif + savollar soni)
         │                             │
         │                             └──► 📝 Ariza qoldirish ──► [Savolnoma]
         │
         ├──► 📋 Ariza qoldirish
         │         │
         │         └──► Vakansiyani tanlash
         │                   │
         │                   └──► Savol 1/N ──► Savol 2/N ──► ... ──► PDF tayyor!
         │                                                                  │
         │                                                    ┌─────────────┴─────────────┐
         │                                                    │                           │
         │                                              ✅ Tasdiqlash              🔄 Qaytadan
         │                                                    │
         │                                             Kanalga yuboriladi
         │
         ├──► 📋 Tez-tez so'raladigan savollar
         │         │
         │         └──► Savollar ro'yxati ──► Savol + Javob
         │
         └──► 🤖 AI yordamchi
                   │
                   └──► ChatGPT bilan suhbat (kompaniya, vakansiya haqida)
                             │
                             └──► ❌ Suhbatni tugatish ──► Asosiy menyu
```

---

## 🛠 Admin panel

```
/admin
  │
  └──► 🛠 Admin panel
         │
         ├──► 💼 Vakansiyalar
         │         │
         │         ├──► [Vakansiya nomi] ──► ✏️ Nom · 📝 Tavsif · ⏸ Holat · 🗑 O'chirish
         │         └──► ➕ Qo'shish ──► Nom kiriting ──► Saqlandi
         │
         ├──► ❓ Savollar
         │         │
         │         └──► Vakansiyani tanlash
         │                   │
         │                   ├──► [Savol] ──► ✏️ Matn · 📷 Rasm talabi · 🗑 O'chirish
         │                   └──► ➕ Savol qo'shish ──► Matn ──► Rasm kerakmi? ──► Saqlandi
         │
         ├──► 📋 FAQ boshqaruvi
         │         │
         │         ├──► [FAQ] ──► ✏️ Savol · ✏️ Javob · 🗑 O'chirish
         │         └──► ➕ FAQ qo'shish ──► Savol ──► Javob ──► Saqlandi
         │
         └──► 📢 Reklama
                   │
                   └──► Xabar yuboring ──► Tasdiqlash ──► Hammaga yuborildi ✅
```

---

## 📄 PDF ariza

Har bir ariza uchun **professional PDF** avtomatik yaratiladi:

<table>
<tr>
<th>Element</th>
<th>Tavsif</th>
</tr>
<tr>
<td>🎨 <b>Sarlavha</b></td>
<td>To'q ko'k fon, vakansiya nomi va sana</td>
</tr>
<tr>
<td>🔢 <b>Savol raqami</b></td>
<td>Ko'k rang ko'rinishdagi raqamli belgi (1, 2, 3...)</td>
</tr>
<tr>
<td>📷 <b>Rasm</b></td>
<td>Savol kartochkasining yuqori qismida joylashadi</td>
</tr>
<tr>
<td>💬 <b>Javob bloki</b></td>
<td>Oq fon, ramka ichida nomzodning javobi</td>
</tr>
<tr>
<td>📏 <b>Chap aksent chiziq</b></td>
<td>Har bir savol kartochkasida ko'k vertikal chiziq</td>
</tr>
<tr>
<td>📅 <b>Pastki qism</b></td>
<td>Sana, vaqt va "Telegram bot orqali to'ldirildi" yozuvi</td>
</tr>
</table>

> **Katta rasmlar uchun himoya:** 8MB dan katta yoki 2400px dan katta rasmlar avtomatik o'lchamini kamaytiradi. Agar PDF yaratishda xato bo'lsa — rasmsiz qayta yaratiladi.

---

## 📦 Kutubxonalar

<div align="center">

| Kutubxona | Versiya | Vazifasi |
|-----------|:-------:|---------|
| `aiogram` | `^3.13` | Telegram Bot framework |
| `sqlalchemy[asyncio]` | `^2.0` | Asinxron ORM |
| `asyncpg` | `^0.30` | PostgreSQL drayveri |
| `python-dotenv` | `^1.0` | `.env` fayl yuklash |
| `reportlab` | `^4.2` | PDF yaratish |
| `Pillow` | `^11.0` | Rasm qayta ishlash |
| `openai` | `^1.30` | ChatGPT API |
| `aiofiles` | `^24.1` | Asinxron fayl amallari |

</div>

---

## 🔒 Xavfsizlik

- 🔐 Barcha maxfiy ma'lumotlar `.env` faylida saqlanadi (repozitoriyga **kirmaydi**)
- 🛡 Barcha admin amallari `AdminFilter` orqali himoyalangan
- 📋 `.env.example` — haqiqiy ma'lumotlarsiz shablon fayl
- 🗑 Vaqtinchalik fayllar (rasm, PDF) ishlatilgandan so'ng darhol o'chiriladi

---

## 🤝 Hissa qo'shish

```bash
# 1. Fork qiling
# 2. Yangi branch oching
git checkout -b feature/yangi-funksiya

# 3. O'zgarishlar kiriting
git commit -m "feat: yangi funksiya qo'shildi"

# 4. Push qiling
git push origin feature/yangi-funksiya

# 5. Pull Request oching
```

---

<div align="center">

## 📬 Aloqa

[![GitHub](https://img.shields.io/badge/GitHub-SunnatDevPy-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/SunnatDevPy)
[![Telegram](https://img.shields.io/badge/Telegram-@SunnatDev-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/SunnatDev)

---

**📝 Litsenziya:** MIT © 2026 [SunnatDevPy](https://github.com/SunnatDevPy)

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:2b6cb0,100:1a365d&height=100&section=footer" width="100%"/>

</div>
