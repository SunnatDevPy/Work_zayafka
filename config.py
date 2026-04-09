import os

from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids() -> list[int]:
    ids: list[int] = []
    for key in ("ADMIN", "ANOTHER_ADMIN"):
        raw = os.getenv(key)
        if not raw:
            continue
        for part in raw.replace(",", " ").split():
            part = part.strip()
            if not part:
                continue
            try:
                ids.append(int(part))
            except ValueError:
                continue
    return list(dict.fromkeys(ids))


class DbConfig:
    def __init__(self) -> None:
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASS", "")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME", "postgres")
        self.db_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


class BotConfig:
    token: str = os.getenv("BOT_TOKEN", "").strip()
    admin_ids: list[int] = _parse_admin_ids()
    target_chat_id: str | None = os.getenv("GROUP_OR_CHANNEL_ID") or os.getenv("TARGET_CHAT_ID")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    def homework_invite_text(self, lang: str = "uz") -> str:
        from locales.messages import LANG_RU, norm_lang

        lg = norm_lang(lang)
        default_ru = (
            "🎉 Ваша заявка <b>принята</b>.\n\n"
            "📎 Ниже текст задания и при необходимости тестовый PDF.\n"
            "✏️ После выполнения нажмите «Отправить задание» — бот примет ваш ответ."
        )
        default_uz = (
            "🎉 Arizangiz <b>qabul qilindi</b>.\n\n"
            "📎 Quyida vazifa matni va kerak bo‘lsa test PDF fayl.\n"
            "✏️ Ishni bajargach «Vazifani yuborish» tugmasini bosing — bot javoblaringizni qabul qiladi."
        )
        if lg == LANG_RU:
            raw = os.getenv("HOMEWORK_TEXT_RU") or os.getenv("HOMEWORK_TEXT")
            return raw if raw and raw.strip() else default_ru
        raw = os.getenv("HOMEWORK_TEXT")
        return raw if raw and raw.strip() else default_uz

    def homework_pdf_path(self) -> str | None:
        p = os.getenv("HOMEWORK_SAMPLE_PDF")
        if not p or not str(p).strip():
            return None
        return str(p).strip()


class Conf:
    db = DbConfig()
    bot = BotConfig()


conf = Conf()
