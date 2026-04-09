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
from keyboards.inline import language_pick_kb
from locales.messages import LANG_UZ, all_labels, msg, norm_lang, pick_language_prompt
from services.ai import ask_openai
from utils.user_locale import get_user_locale

router = Router(name="ai_chat")
logger = logging.getLogger(__name__)


class AIChatState(StatesGroup):
    chatting = State()


def _chat_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=msg(lang, "btn_ai_exit"))]],
        resize_keyboard=True,
    )


async def _ai_lang(telegram_id: int) -> str:
    loc = await get_user_locale(telegram_id)
    return norm_lang(loc) if loc else LANG_UZ


# ─────────────────────────── Enter chat ─────────────────────────────

@router.message(F.text.in_(all_labels("btn_ai")))
async def start_ai_chat(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    if not await get_user_locale(message.from_user.id):
        await message.answer(pick_language_prompt(), reply_markup=language_pick_kb())
        return
    lang = await _ai_lang(message.from_user.id)
    if not conf.bot.openai_api_key:
        await message.answer(msg(lang, "ai_off"))
        return

    await state.set_state(AIChatState.chatting)
    await state.update_data(history=[], ai_ui_lang=lang)
    await message.answer(msg(lang, "ai_welcome"), reply_markup=_chat_kb(lang))


# ─────────────────────────── Exit chat ──────────────────────────────

@router.message(F.text.in_(all_labels("btn_ai_exit")), AIChatState.chatting)
@router.message(Command("stop"), AIChatState.chatting)
async def exit_ai_chat(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("ai_ui_lang") or LANG_UZ
    await state.clear()
    from handlers.user import _main_kb

    await message.answer(msg(lang, "ai_exit_done"), reply_markup=_main_kb(lang))


# ─────────────────────────── Handle messages ────────────────────────

@router.message(AIChatState.chatting)
async def handle_ai_message(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("ai_ui_lang") or LANG_UZ

    if not message.text:
        await message.answer(msg(lang, "ai_text_only"))
        return

    user_text = message.text.strip()
    if not user_text:
        return

    thinking = await message.answer(msg(lang, "ai_thinking"))

    history: list[dict] = data.get("history") or []

    try:
        answer = await ask_openai(
            api_key=conf.bot.openai_api_key,
            history=history,
            user_message=user_text,
        )
    except ValueError as exc:
        await _delete_safe(thinking)
        await message.answer(f"⚠️ {escape(str(exc))}")
        return
    except Exception:
        await _delete_safe(thinking)
        await message.answer(msg(lang, "ai_error_generic"))
        return

    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": answer})
    if len(history) > 20:
        history = history[-20:]
    await state.update_data(history=history)

    await _delete_safe(thinking)
    await message.answer(f"🤖 {escape(answer)}")


async def _delete_safe(m: Message) -> None:
    try:
        await m.delete()
    except TelegramBadRequest:
        pass
