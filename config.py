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


class Conf:
    db = DbConfig()
    bot = BotConfig()


conf = Conf()
