"""AI assistant chat handler — powered by OpenAI ChatGPT."""

import logging
from html import escape

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from config import conf
from services.ai import ask_openai

router = Router(name="ai_chat")
logger = logging.getLogger(__name__)

AI_BTN_ENTER = "🤖 AI yordamchi"
AI_BTN_EXIT  = "❌ Suhbatni tugatish"

_WELCOME = (
    "🤖 <b>AI Yordamchi</b>\n\n"
    "Kompaniyamiz, vakansiyalar va ish sharoitlari haqida savollaringizga javob beraman.\n\n"
    "<b>Misol savollar:</b>\n"
    "• Qanday vakansiyalar mavjud?\n"
    "• Ish haqi va bonuslar qanday?\n"
    "• Ariza berish uchun nima kerak?\n"
    "• Ish grafigi qanday?\n\n"
    "💬 Savolingizni yozing 👇"
)


class AIChatState(StatesGroup):
    chatting = State()


def _chat_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=AI_BTN_EXIT)]],
        resize_keyboard=True,
    )


# ─────────────────────────── Enter chat ─────────────────────────────

@router.message(F.text == AI_BTN_ENTER)
async def start_ai_chat(message: Message, state: FSMContext) -> None:
    if not conf.bot.openai_api_key:
        await message.answer(
            "⚠️ <b>AI yordamchi hozirda ulangan emas.</b>\n\n"
            "Administrator tez orada sozlaydi."
        )
        return

    await state.set_state(AIChatState.chatting)
    await state.update_data(history=[])
    await message.answer(_WELCOME, reply_markup=_chat_kb())


# ─────────────────────────── Exit chat ──────────────────────────────

@router.message(F.text == AI_BTN_EXIT, AIChatState.chatting)
@router.message(Command("stop"), AIChatState.chatting)
async def exit_ai_chat(message: Message, state: FSMContext) -> None:
    await state.clear()
    # Import here to avoid circular dependency
    from handlers.user import _main_kb
    await message.answer(
        "👋 Suhbat tugatildi. Istalgan vaqt qaytishingiz mumkin!",
        reply_markup=_main_kb(),
    )


# ─────────────────────────── Handle messages ────────────────────────

@router.message(AIChatState.chatting)
async def handle_ai_message(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("✍️ Iltimos, faqat matnli savol yuboring.")
        return

    user_text = message.text.strip()
    if not user_text:
        return

    # Show "thinking" indicator
    thinking = await message.answer("⏳ Javob tayyorlanmoqda…")

    data = await state.get_data()
    history: list[dict] = data.get("history") or []

    try:
        answer = await ask_openai(
            api_key=conf.bot.openai_api_key,
            history=history,
            user_message=user_text,
        )
    except ValueError as exc:
        # Known errors (wrong key, rate limit)
        await _delete_safe(thinking)
        await message.answer(f"⚠️ {escape(str(exc))}")
        return
    except Exception:
        await _delete_safe(thinking)
        await message.answer("⚠️ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        return

    # Update conversation history (keep last 20 entries = 10 exchanges)
    history.append({"role": "user",      "content": user_text})
    history.append({"role": "assistant", "content": answer})
    if len(history) > 20:
        history = history[-20:]
    await state.update_data(history=history)

    await _delete_safe(thinking)
    await message.answer(f"🤖 {escape(answer)}")


async def _delete_safe(msg: Message) -> None:
    try:
        await msg.delete()
    except TelegramBadRequest:
        pass
