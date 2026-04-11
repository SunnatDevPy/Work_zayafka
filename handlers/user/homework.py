from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup

from config import conf


router = Router(name="user_homework")


USER_BTN_APPLY = "📋 Ariza qoldirish"
USER_BTN_VIEW = "🔍 Vakansiyalarni ko‘rish"
USER_BTN_AI = "🤖 AI yordamchi"
USER_BTN_FAQ = "📋 Tez-tez so‘raladigan savollar"


def _main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=USER_BTN_VIEW), KeyboardButton(text=USER_BTN_FAQ)],
            [KeyboardButton(text=USER_BTN_AI)],
            [KeyboardButton(text=USER_BTN_APPLY)],
        ],
        resize_keyboard=True,
    )


class HomeworkStates(StatesGroup):
    collecting = State()


@router.callback_query(F.data == "hw:go")
async def homework_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.set_state(HomeworkStates.collecting)
    await state.update_data(hw_items=[])
    await query.message.answer(
        "📤 Bajarilgan vazifani yuboring: matn, fayl, rasm yoki video.\n"
        "✅ Hammasi tayyor bo‘lsa — «Tayyor» tugmasini bosing.\n\n"
        "⛔️ Bekor: /cancel",

    )


@router.callback_query(F.data == "hw:done")
async def homework_done(query: CallbackQuery, state: FSMContext) -> None:
    cur = await state.get_state()
    if cur != HomeworkStates.collecting.state:
        await query.answer("Avvalo «Vazifani yuborish» tugmasini bosing.", show_alert=True)
        return
    await query.answer("✅ Qabul qilindi")
    data = await state.get_data()
    items: list = data.get("hw_items") or []
    await state.clear()
    n = len(items)
    await query.message.answer(
        f"🎉 Rahmat! Qabul qilingan materiallar: {n} ta.",
        reply_markup=_main_kb(),
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
    await state.clear()
    await message.answer("❌ Vazifa qabul qilish bekor qilindi.", reply_markup=_main_kb())


@router.message(HomeworkStates.collecting)
async def homework_collect(message: Message, state: FSMContext) -> None:
    if message.text and message.text.startswith("/"):
        await message.answer("⛔️ Bekor qilish uchun /cancel yuboring.")
        return
    data = await state.get_data()
    items: list = list(data.get("hw_items") or [])
    if message.text:
        items.append({"kind": "text", "text": message.text[:4000]})
    elif message.document:
        items.append({"kind": "doc", "file_id": message.document.file_id, "name": message.document.file_name or "file"})
    elif message.photo:
        items.append({"kind": "photo", "file_id": message.photo[-1].file_id})
    elif message.video:
        items.append({"kind": "video", "file_id": message.video.file_id})
    elif message.voice:
        items.append({"kind": "voice", "file_id": message.voice.file_id})
    elif message.audio:
        items.append({"kind": "audio", "file_id": message.audio.file_id})
    else:
        await message.answer("📎 Matn, rasm, hujjat, audio yoki video yuboring.")
        return
    await state.update_data(hw_items=items)
    await message.answer(f"✅ Saqlandi ({len(items)} ta). Yana yuborishingiz yoki «Tayyor» tugmasini bosing.")

