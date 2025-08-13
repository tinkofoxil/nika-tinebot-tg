import os
import asyncio
from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from dotenv import load_dotenv
load_dotenv()

# ==== настройки ====
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Положи TELEGRAM_BOT_TOKEN в .env или окружение")

bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# ==== состояния ====
class Form(StatesGroup):
    gender = State()
    source = State()

def kb_gender() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨 Мужчина", callback_data="g_male")],
        [InlineKeyboardButton(text="👩 Женщина", callback_data="g_female")],
    ])

def kb_source() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="От друзей", callback_data="s_friends")],
        [InlineKeyboardButton(text="Из других каналов", callback_data="s_channels")],
    ])

# ==== хендлеры ====
@router.message(CommandStart())
async def start(msg: Message, state: FSMContext):
    await msg.answer("Ваш личный ассистент <b>Ника</b> почти готов к работе…\nЗагружаюсь…")
    await asyncio.sleep(5)  # пауза как в блоке «Задержка»
    await state.set_state(Form.gender)
    await msg.answer(
        f"Привет, <b>{msg.from_user.first_name or 'друг'}</b>!\n"
        "Давай познакомимся 🤗\nКакого ты пола?",
        reply_markup=kb_gender()
    )

@router.callback_query(Form.gender, F.data.startswith("g_"))
async def gender_chosen(call: CallbackQuery, state: FSMContext):
    gender = call.data.split("_", 1)[1]   # male / female
    await state.update_data(gender=gender)
    await call.message.edit_reply_markup()
    await state.set_state(Form.source)
    await call.message.answer("Супер! Как ты о нас узнал?", reply_markup=kb_source())

@router.callback_query(Form.source, F.data.startswith("s_"))
async def source_chosen(call: CallbackQuery, state: FSMContext):
    source = call.data.split("_", 1)[1]   # friends / channels
    data = await state.update_data(source=source)
    await call.message.edit_reply_markup()

    gender_txt = "Мужчина" if data["gender"] == "male" else "Женщина"
    source_txt = "От друзей" if source == "friends" else "Из других каналов"

    await call.message.answer(
        f"Спасибо за ответы! 🔥\n<i>Пол</i>: {gender_txt}\n<i>Источник</i>: {source_txt}\n\n"
        "Скоро пришлю информацию о программе и кнопку оплаты."
    )
    await state.clear()

# ==== запуск ====
def main():
    import logging
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    main()
