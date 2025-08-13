import os
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
)
from dotenv import load_dotenv

load_dotenv()

# ==== настройки ====
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # опционально: чат/юзер, куда слать уведомление
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
    nicotine = State()
    duration = State()
    email = State()

# ==== клавиатуры ====

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


def kb_nicotine() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сигареты", callback_data="n_cigs")],
        [InlineKeyboardButton(text="Одноразовые испарители", callback_data="n_disposables")],
        [InlineKeyboardButton(text="Снюс", callback_data="n_snus")],
        [InlineKeyboardButton(text="Нагреватели табака", callback_data="n_heaters")],
        [InlineKeyboardButton(text="Вейпы", callback_data="n_vapes")],
    ])


def kb_duration() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Меньше года", callback_data="d_<1")],
        [InlineKeyboardButton(text="1–3 года", callback_data="d_1-3")],
        [InlineKeyboardButton(text="3–5 лет", callback_data="d_3-5")],
        [InlineKeyboardButton(text="5 лет и более", callback_data="d_5+")],
    ])


def kb_one(text: str, cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=cb)]])

# ==== тексты ====
CONSENT_TEXT = """И последнее: введи, пожалуйста, свой e-mail ✉️
Ника не любит спам и не шлёт лишнего — только полезные письма с материалами и твоими результатами.

Вводя почту, ты подтверждаешь согласие на обработку и хранение персональных данных.
"""

INTRO_1 = """Я — высокотехнологичный ИИ ассистент Ника 🤖
Меня создали команда из аддиктолога и психотерапевта НМИЦ им. Бехтерева, а также специалисты из Сколково.
"""

INTRO_2 = """Мои создатели сделали всё, чтобы я позаботилась о твоём здоровье и помогла бросить никотин.
Я обучена на базе знаний: более 200 исследований, 15 эффективных методик, опыт лечения за 50 лет.
"""

INTRO_3 = """Заинтриговала? Это программа по избавлению от никотиновой зависимости на 30 дней — доступна каждому.
Ты сможешь бросить без срывов, без набора веса и без перехода на другой источник никотина.
"""

INTRO_4 = """Ты бросишь зависимость без последствий:
• без переедания и набора веса
• без рецидивов и срывов в будущем
• без перехода на другой источник никотина
• эффект даже после алкоголя
"""

INTRO_5 = """План программы: каждый день я буду присылать короткий план из нескольких шагов.
Следуя ему, бросить курить становится реальнее и проще.
"""

INTRO_6 = """У нас десятки реальных историй и отзывов. Скоро покажу примеры дня и дам возможность оформить доступ.
"""

RESULTS_TEXT = """Конечно есть! И результаты очень впечатляющие, как по мне 🙂
Мы собираем статистику по прохождению программы и видим стабильное улучшение показателей.

Готов идти дальше?
"""

ARTICLE_TEXT = """А это — небольшая статья о том, как отказ от никотина меняет организм и жизнь участников программы.
Прочитать можно по ссылке: https://clck.ru/3NGJN2

Идём дальше?
"""

PRICING_TEXT = """Если тебе было интересно почитать истории участников, логичный вопрос — сколько стоит программа?

Мы долго сравнивали со стоимостью заменителей (жвачки/пластыри) и решили сделать цену доступной.
Обычная стоимость — 1 990 ₽. Но сейчас действует спец-предложение — 1 390 ₽.

Это не подписка: один раз оплатил — и материалы остаются с тобой навсегда. Остаёшься со мной?
"""

BENEFITS_TEXT = """Во время нашей 30-дневной программы ты получишь:
• 15 лучших проверенных методик, чтобы отказаться от никотина
• Занимает 10–15 минут в день
• Построишь полезные привычки
• Более 200 ссылок на исследования

Нажимая «Оплатить» — ты соглашаешься с условиями.
"""

REMIND_TEXT = """Программа рассчитана на 30 дней, плавный выход из зависимости и дальнейшая поддержка.
Короткие задания, дневник, поддержка и техники на каждый день.
"""

REVIEWS_TEXT = """Конечно! Вот несколько отзывов участников:

• «Я бросала курить раз четыре. В этой программе впервые получилось»
• «Здесь не просто “держался”, а реально работал с головой. Спасибо, Ника!»

Вернуться к меню?
"""

DAY_TEXT = """<b>5 день — альтернативы</b>
Чтение займёт ~5 минут.

Готов к первому заданию?
"""

TASK1_TEXT = """Задание 1. Запиши 3 альтернативных действия, которыми заменишь
привычный ритуал с никотином (например, вода, дыхание 4-7-8, короткая прогулка).
"""


# ==== хендлеры ====
@router.message(CommandStart())
async def start(msg: Message, state: FSMContext):
    await msg.answer("Ваш личный ассистент <b>Ника</b> почти готов к работе…\nЗагружаюсь…")
    await asyncio.sleep(5)  # пауза как в блоке «Задержка»

    await state.set_state(Form.gender)
    await msg.answer(
        f"Привет, <b>{msg.from_user.first_name or 'друг'}</b>!\n"
        "Давай познакомимся 🤗\nКакого ты пола?",
        reply_markup=kb_gender(),
    )


@router.callback_query(Form.gender, F.data.startswith("g_"))
async def gender_chosen(call: CallbackQuery, state: FSMContext):
    gender = call.data.split("_", 1)[1]  # male / female
    await state.update_data(gender=gender)
    await call.message.edit_reply_markup()

    await state.set_state(Form.source)
    await call.message.answer("Супер! Как ты о нас узнал?", reply_markup=kb_source())


@router.callback_query(Form.source, F.data.startswith("s_"))
async def source_chosen(call: CallbackQuery, state: FSMContext):
    source = call.data.split("_", 1)[1]  # friends / channels
    await state.update_data(source=source)
    await call.message.edit_reply_markup()

    await state.set_state(Form.nicotine)
    await call.message.answer("Какой тип никотина ты используешь?", reply_markup=kb_nicotine())


@router.callback_query(Form.nicotine, F.data.startswith("n_"))
async def nicotine_chosen(call: CallbackQuery, state: FSMContext):
    nicotine = call.data.split("_", 1)[1]
    await state.update_data(nicotine=nicotine)
    await call.message.edit_reply_markup()

    await state.set_state(Form.duration)
    await call.message.answer("Спасибо! Как давно ты начал(а) употреблять табачные изделия?", reply_markup=kb_duration())


@router.callback_query(Form.duration, F.data.startswith("d_"))
async def duration_chosen(call: CallbackQuery, state: FSMContext):
    duration = call.data.split("_", 1)[1]
    await state.update_data(duration=duration)
    await call.message.edit_reply_markup()

    await state.set_state(Form.email)
    await call.message.answer(CONSENT_TEXT)


@router.message(Form.email)
async def email_received(msg: Message, state: FSMContext):
    email = msg.text.strip()
    if "@" not in email or "." not in email or len(email) < 5:
        return await msg.answer("Это не совсем похоже на почту! Перепроверь, пожалуйста.")

    data = await state.update_data(email=email)

    # уведомление админу (если указан ADMIN_CHAT_ID)
    if ADMIN_CHAT_ID:
        try:
            user = msg.from_user
            gender_txt = "Мужчина" if data.get("gender") == "male" else "Женщина"
            source_txt = "От друзей" if data.get("source") == "friends" else "Из других каналов"
            await bot.send_message(
                int(ADMIN_CHAT_ID),
                (
                    "👤 <b>Новая анкета</b>\n"
                    f"ID: <code>{user.id}</code> (@{user.username or '—'})\n"
                    f"Имя: {user.full_name}\n"
                    f"Пол: {gender_txt}\nИсточник: {source_txt}\n"
                    f"Никотин: {data.get('nicotine')} | Стаж: {data.get('duration')}\n"
                    f"Email: {email}"
                ),
            )
        except Exception:
            pass

    # мини-путешествие
    await msg.answer("Теперь мы отправляемся в короткое путешествие… ✨")
    await asyncio.sleep(2)

    # старт презентационного блока
    await send_intro_1(msg.chat.id)

    await state.clear()


# ====== серия экранов «о программе» ======
async def send_intro_1(chat_id: int):
    await bot.send_message(chat_id, INTRO_1, reply_markup=kb_one("А что ты умеешь?", "i_abilities"))


@router.callback_query(F.data == "i_abilities")
async def intro_abilities(call: CallbackQuery):
    await call.message.edit_reply_markup()
    await call.message.answer(INTRO_2, reply_markup=kb_one("А что за программа?", "i_program"))


@router.callback_query(F.data == "i_program")
async def intro_program(call: CallbackQuery):
    await call.message.edit_reply_markup()
    await call.message.answer(INTRO_3, reply_markup=kb_one("И что же главное?", "i_main"))


@router.callback_query(F.data == "i_main")
async def intro_main(call: CallbackQuery):
    await call.message.edit_reply_markup()
    await call.message.answer(INTRO_4, reply_markup=kb_one("Но как?", "i_how"))


@router.callback_query(F.data == "i_how")
async def intro_how(call: CallbackQuery):
    await call.message.edit_reply_markup()
    await call.message.answer(INTRO_5, reply_markup=kb_one("А есть результаты?", "i_results"))


@router.callback_query(F.data == "i_results")
async def intro_results(call: CallbackQuery):
    await call.message.edit_reply_markup()
    # Показываем блок с результатами и кнопкой «дальше»
    await call.message.answer(RESULTS_TEXT, reply_markup=kb_one("Впечатляет, давай дальше", "go_article"))


@router.callback_query(F.data == "go_article")
async def go_article(call: CallbackQuery):
    await call.message.edit_reply_markup()
    await call.message.answer(ARTICLE_TEXT, reply_markup=kb_one("Дальше", "go_pricing"))


@router.callback_query(F.data == "go_pricing")
async def go_pricing(call: CallbackQuery):
    await call.message.edit_reply_markup()
    await call.message.answer(PRICING_TEXT, reply_markup=kb_one("Да!", "pay_yes"))


@router.callback_query(F.data == "pay_yes")
async def pay_yes(call: CallbackQuery):
    await call.message.edit_reply_markup()
    # Показываем меню из 4 пунктов: вперёд, отзывы, напомни программу, пример дня
    await show_after_yes_menu(call.message.chat.id)
    return

async def show_after_yes_menu(chat_id: int):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вперёд 🔥", callback_data="go_offer")],
        [InlineKeyboardButton(text="А есть отзывы?", callback_data="show_reviews")],
        [InlineKeyboardButton(text="Напомни, какая программа", callback_data="remind_program")],
        [InlineKeyboardButton(text="Покажи пример дня", callback_data="sample_day")],
    ])
    await bot.send_message(
        chat_id,
        """Чтобы курение осталось в прошлом, я пришлю тебе индивидуальную программу.

        "Скорее жми \"Вперёд 🔥\" — и отправлю ссылку на оплату!""",
        reply_markup=kb,
    )

@router.callback_query(F.data == "go_offer")
async def go_offer(call: CallbackQuery):
    await call.message.edit_reply_markup()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплата 1390₽ 🔥", callback_data="pay_1390")],
        [InlineKeyboardButton(text="Назад", callback_data="menu_back")],
    ])
    await call.message.answer(BENEFITS_TEXT, reply_markup=kb)


@router.callback_query(F.data == "remind_program")
async def remind_program(call: CallbackQuery):
    await call.message.edit_reply_markup()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплата 1390₽ 🔥", callback_data="pay_1390")],
        [InlineKeyboardButton(text="Назад", callback_data="menu_back")],
    ])
    await call.message.answer(REMIND_TEXT, reply_markup=kb)


@router.callback_query(F.data == "show_reviews")
async def show_reviews(call: CallbackQuery):
    await call.message.edit_reply_markup()
    await call.message.answer(REVIEWS_TEXT, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="menu_back")]]))

@router.callback_query(F.data == "sample_day")
async def sample_day(call: CallbackQuery):
    await call.message.edit_reply_markup()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Задание 1", callback_data="day_task1")]])
    await call.message.answer(DAY_TEXT, reply_markup=kb)

@router.callback_query(F.data == "day_task1")
async def day_task1(call: CallbackQuery):
    await call.message.edit_reply_markup()
    await call.message.answer(TASK1_TEXT)
    await asyncio.sleep(5)
    await call.message.answer(
        "Вернёмся к программе?", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Пожалуй да, пора начать", callback_data="menu_back")]])
    )

# --- Назад в меню после «Да!» ---
@router.callback_query(F.data == "menu_back")
async def menu_back(call: CallbackQuery):
    await call.message.edit_reply_markup()
    await show_after_yes_menu(call.message.chat.id)

# --- Оплата (пока заглушка) ---
@router.callback_query(F.data == "pay_1390")
async def pay_1390(call: CallbackQuery):
    await call.message.edit_reply_markup()
    await call.message.answer("Пару минут! Проверяю оплату ☑️")
    await asyncio.sleep(3)
    await call.message.answer(
        "Оплату подключим на следующем шаге. Пока можешь посмотреть пример дня или отзывы.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="menu_back")]])
    )


async def intro_results(call: CallbackQuery):
    pass  # заглушка, чтобы не ломать поиск по имени(call: CallbackQuery):
    await call.message.edit_reply_markup()
    await call.message.answer(INTRO_6)
    # сюда позже добавим: показать отзывы / пример дня / кнопку «Оплатить»


# ==== запуск ====

def main():
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
