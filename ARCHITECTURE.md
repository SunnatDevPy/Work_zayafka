# Architecture

Loyiha soddalashtirilgan qatlamli tuzilmaga o'tkazildi:

## Qatlamlar

- `app/` — startup va wiring (bot/dispatcher factory, router include, polling start)
- `handlers/` — Telegram update handling (admin, user, FAQ, AI chat, review)
- `models/` — SQLAlchemy ORM modellari va DB session
- `services/` — tashqi servislar (PDF, OpenAI)
- `keyboards/` — inline/reply keyboard builderlar
- `utils/` — yordamchi filter va utility lar

## Entry Point

- `main.py` faqat `run_polling()` ni ishga tushiradi.

## Startup Flow

1. `app.run.run_polling()`
2. DB table init (`db.create_all()`)
3. Bot/Dispatcher yaratish (`app.factory`)
4. Routerlarni ulash (`include_routers`)
5. `/start` komandani set qilish
6. Polling start

