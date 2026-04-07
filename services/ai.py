"""OpenAI ChatGPT integration for the HR-bot AI assistant."""

import logging
import os

logger = logging.getLogger(__name__)

# ─────────────────────────── Default system prompt ──────────────────
# Переопределяется через переменную окружения AI_SYSTEM_PROMPT
_DEFAULT_PROMPT = """\
Siz [KOMPANIYA NOMI] kompaniyasining rasmiy AI-yordamchisisiz.

FAQAT quyidagi mavzular bo'yicha javob bering:
• Kompaniya haqida umumiy ma'lumot (tarixi, faoliyati, qadriyatlari)
• Mavjud vakansiyalar: lavozim, talablar, ish haqi, ish joyi
• Ish sharoitlari, ish vaqti, bonuslar va imtiyozlar
• Ariza berish jarayoni va bosqichlari
• Nomzodlarga qo'yiladigan umumiy talablar

Agar savol ushbu mavzulardan TASHQARIDA bo'lsa:
"Bu savol mening vakolatimdan tashqarida. Kompaniyamiz vakansiyalari yoki ish sharoitlari haqida so'rasangiz, yordam bera olaman!" deb javob bering.

Qoidalar:
- Javoblar qisqa (3-6 jumla) va aniq bo'lsin
- Doimo do'stona va professional ohangda
- O'zbek tilida javob bering
- Formatlash uchun faqat oddiy belgilar ishlating: •, -, raqamlar
- HTML yoki markdown belgilarini ishlatmang
"""

SYSTEM_PROMPT: str = os.getenv("AI_SYSTEM_PROMPT") or _DEFAULT_PROMPT


async def ask_openai(
    api_key: str,
    history: list[dict],
    user_message: str,
    *,
    system_prompt: str = SYSTEM_PROMPT,
    model: str = "gpt-4o-mini",
    max_tokens: int = 700,
    temperature: float = 0.6,
) -> str:
    """
    Send a message to OpenAI and return the text reply.

    history: list of {"role": "user"/"assistant", "content": "..."}
    Keeps last 12 messages (~6 exchanges) for context window efficiency.
    """
    try:
        from openai import AsyncOpenAI, APIStatusError
    except ImportError:
        raise RuntimeError("openai paketi o'rnatilmagan. 'pip install openai' buyrug'ini ishga tushiring.")

    client = AsyncOpenAI(api_key=api_key)

    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-12:])
    messages.append({"role": "user", "content": user_message})

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = (response.choices[0].message.content or "").strip()
        return text or "Javob olishda xatolik yuz berdi."
    except APIStatusError as exc:
        logger.error("OpenAI API xatosi [%s]: %s", exc.status_code, exc.message)
        if exc.status_code == 401:
            raise ValueError("OPENAI_API_KEY noto'g'ri yoki muddati o'tgan.")
        if exc.status_code == 429:
            raise ValueError("OpenAI limit oshib ketdi. Birozdan so'ng urinib ko'ring.")
        raise
    except Exception as exc:
        logger.error("OpenAI umumiy xato: %s", exc)
        raise
