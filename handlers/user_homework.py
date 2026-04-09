from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import conf
from keyboards.inline import homework_done_kb
from locales.messages import LANG_UZ, msg, norm_lang
from utils.user_locale import get_user_locale

router = Router(name="user_homework")


class HomeworkStates(StatesGroup):
    collecting = State()


async def _hw_lang(telegram_id: int) -> str:
    loc = await get_user_locale(telegram_id)
    return norm_lang(loc) if loc else LANG_UZ


@router.callback_query(F.data == "hw:go")
async def homework_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    uid = query.from_user.id if query.from_user else 0
    lang = await _hw_lang(uid)
    await state.set_state(HomeworkStates.collecting)
    await state.update_data(hw_items=[], hw_ui_lang=lang)
    await query.message.answer(
        msg(lang, "hw_start_text"),
        reply_markup=homework_done_kb(lang),
    )


@router.callback_query(F.data == "hw:done")
async def homework_done(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("hw_ui_lang") or LANG_UZ
    cur = await state.get_state()
    if cur != HomeworkStates.collecting.state:
        await query.answer(msg(lang, "hw_press_first"), show_alert=True)
        return
    await query.answer(msg(lang, "hw_accept"))
    items: list = data.get("hw_items") or []
    await state.clear()
    n = len(items)
    from handlers.user import _main_kb

    await query.message.answer(
        msg(lang, "hw_thanks", n=n),
        reply_markup=_main_kb(lang),
    )
    uname = f"@{query.from_user.username}" if query.from_user and query.from_user.username else "—"
    uid = query.from_user.id if query.from_user else 0
    for aid in conf.bot.admin_ids:
        try:
            await query.bot.send_message(
                aid,
                f"📥 Vazifa topshirildi: foydalanuvchi {uid} {uname}. Materiallar: {n} ta.",
            )
        except Exception:
            pass


@router.message(Command("cancel"), HomeworkStates.collecting)
async def homework_cancel(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("hw_ui_lang") or LANG_UZ
    await state.clear()
    from handlers.user import _main_kb

    await message.answer(msg(lang, "hw_cancel"), reply_markup=_main_kb(lang))


@router.message(HomeworkStates.collecting)
async def homework_collect(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("hw_ui_lang") or LANG_UZ
    if message.text and message.text.startswith("/"):
        await message.answer(msg(lang, "hw_use_cancel"))
        return
    items: list = list(data.get("hw_items") or [])
    if message.text:
        items.append({"kind": "text", "text": message.text[:4000]})
    elif message.document:
        items.append(
            {
                "kind": "doc",
                "file_id": message.document.file_id,
                "name": message.document.file_name or "file",
            }
        )
    elif message.photo:
        items.append({"kind": "photo", "file_id": message.photo[-1].file_id})
    elif message.video:
        items.append({"kind": "video", "file_id": message.video.file_id})
    elif message.voice:
        items.append({"kind": "voice", "file_id": message.voice.file_id})
    elif message.audio:
        items.append({"kind": "audio", "file_id": message.audio.file_id})
    else:
        await message.answer(msg(lang, "hw_send_types"))
        return
    await state.update_data(hw_items=items)
    await message.answer(msg(lang, "hw_saved", n=len(items)))
