import asyncio

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select

from models.bot_user import BotUser
from models.database import db
from utils.filters import AdminFilter

router = Router(name="admin_broadcast")


class BroadcastSG(StatesGroup):
    waiting = State()
    confirm = State()


async def _edit_or_answer(query: CallbackQuery, text: str, reply_markup=None) -> None:
    try:
        await query.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        await query.message.answer(text, reply_markup=reply_markup)


@router.callback_query(F.data == "adm:bc", AdminFilter())
async def adm_bc_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.set_state(BroadcastSG.waiting)
    r = await db.execute(select(func.count()).select_from(BotUser))
    n = int(r.scalar() or 0)
    await _edit_or_answer(
        query,
        f"📢 Keyingi xabaringiz <b>{n} ta</b> foydalanuvchiga yuboriladi.\n"
        f"Xabarni yuboring (matn, rasm, video …).",
    )


@router.message(BroadcastSG.waiting, AdminFilter())
async def adm_bc_receive(message: Message, state: FSMContext) -> None:
    await state.update_data(bc_chat_id=message.chat.id, bc_message_id=message.message_id)
    await state.set_state(BroadcastSG.confirm)
    from keyboards.inline import broadcast_confirm_kb
    await message.answer("📤 Bu xabarni hammaga yuboraylikmi?", reply_markup=broadcast_confirm_kb())


@router.callback_query(F.data == "bc:cancel", AdminFilter())
async def adm_bc_cancel(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer("❌ Bekor qilindi")
    await state.clear()
    await _edit_or_answer(query, "❌ Reklama bekor qilindi.")


@router.callback_query(F.data == "bc:send", AdminFilter(), StateFilter(BroadcastSG.confirm))
async def adm_bc_send(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer("📤 Yuborilmoqda…")
    data = await state.get_data()
    chat_id = data.get("bc_chat_id")
    mid = data.get("bc_message_id")
    await state.clear()
    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    if not chat_id or not mid:
        await query.message.answer("⚠️ Yuborish uchun ma'lumot yo'q.")
        return

    r = await db.execute(select(BotUser.telegram_id))
    ids = list(r.scalars().all())
    ok = fail = 0
    for uid in ids:
        try:
            await query.bot.copy_message(chat_id=uid, from_chat_id=chat_id, message_id=mid)
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.04)
    await query.message.answer(f"✅ Tayyor: yuborildi {ok}, xato {fail}.")

