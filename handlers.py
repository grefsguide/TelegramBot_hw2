from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app import get_weather, get_food_info, try_get_food_info, get_workout_info, translate
from states import Form
import logging


router = Router()

# Хранилище данных пользователей
users = {}

buttons = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Внести выпитую воду", callback_data="log_water")],
                [InlineKeyboardButton(text="Внести съеденную еду", callback_data="log_food")],
                [InlineKeyboardButton(text="Внести тренировку", callback_data="log_workout")],
                [InlineKeyboardButton(text="Проверить прогресс", callback_data="check_progress")]
            ]
        )
btnstrt = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Настроить профиль", callback_data="set_profile")]])

sex_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Мужчина", callback_data="sex_male")],
    [InlineKeyboardButton(text="Женщина", callback_data="sex_female")]
    ]
)

@router.message(Command('start'))
async def cmd_start(message: Message):
    button = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Настроить профиль", callback_data="set_profile")]
        ]
    )
    await message.reply("Здравствуйте! Я бот для трекинга здоровья. Нажмите 'Настроить профиль', чтобы начать.", reply_markup=button)


@router.callback_query(lambda c: c.data == "set_profile")
async def process_set_profile(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ваше имя:")
    await state.set_state(Form.name)


@router.message(Form.name)
async def set_name(message: Message, state: FSMContext):
    users[message.from_user.id] = {"name": message.text}
    await message.reply("Какой у вас пол?", reply_markup=sex_keyboard)
    await state.set_state(Form.sex)


@router.callback_query(lambda c: c.data in ["sex_male", "sex_female"])
async def set_sex(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if callback.data == "sex_male":
        users[user_id]["sex"] = 1  # Мужчина
    elif callback.data == "sex_female":
        users[user_id]["sex"] = 0  # Женщина

    await callback.message.edit_text("Введите ваш вес (в кг):")
    await state.set_state(Form.weight)


@router.message(Form.weight)
async def set_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
        users[message.from_user.id]["weight"] = weight
        await message.reply("Введите ваш рост (в см):")
        await state.set_state(Form.height)
    except ValueError:
        await message.reply("Введите корректное число.")


@router.message(Form.height)
async def set_height(message: Message, state: FSMContext):
    try:
        height = float(message.text)
        users[message.from_user.id]["height"] = height
        await message.reply("Введите ваш возраст:")
        await state.set_state(Form.age)
    except ValueError:
        await message.reply("Введите корректное значение.")


@router.message(Form.age)
async def set_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        users[message.from_user.id]["age"] = age
        await message.reply("Сколько минут активности у вас в день?")
        await state.set_state(Form.activity)
    except ValueError:
        await message.reply("Введите корректное значение.")


@router.message(Form.activity)
async def set_activity(message: Message, state: FSMContext):
    try:
        activity = int(message.text)
        users[message.from_user.id]["activity"] = activity
        await message.reply("В каком городе вы находитесь?")
        await state.set_state(Form.city)
    except ValueError:
        await message.reply("Введите корректное значение.")

@router.message(Form.city)
async def set_city(message: Message, state: FSMContext):
    city = message.text
    try:
        weather_data = await get_weather(city)
        temperature = weather_data['main']['temp']

        user = users[message.from_user.id]
        weight = user["weight"]
        height = user["height"]
        age = user["age"]
        activity = user["activity"]
        sex = user["sex"]

        water_goal = weight * 30 + (500 * (activity // 30))
        if temperature > 25:
            water_goal += 500
        if sex == 1:
            calorie_goal = round(88.36 + (weight * 13.4) + (height * 5) - (age * 5.7), 1)
        else:
            calorie_goal = round(447.6 + (weight * 9.2) + (height * 3.1) - (age * 4.3), 1)

        user.update({
            "city": city,
            "water_goal": water_goal,
            "calorie_goal": calorie_goal,
            "logged_water": 0,
            "logged_calories": 0,
            "burned_calories": 0
        })

        await message.reply(
            f"Профиль настроен!\n"
            f"Текущая температура в {city}: {temperature}°C\n"
            f"Норма воды: {water_goal} мл\n"
            f"Норма калорий: {calorie_goal} ккал.",
            reply_markup=buttons
        )
        await state.clear()
    except Exception as e:
        await message.reply(f"Ошибка при получении данных о погоде: {e}")
# Логирование выпитой воды
@router.callback_query(lambda c: c.data == "log_water")
async def log_water(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.logget_water)
    await callback.message.edit_text("Введите количество воды (в мл), которую вы выпили:")

@router.message(Form.logget_water)
async def log_water(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    current_amount = data.get('water_amount', 0)

    try:
        # Парсим количество воды из сообщения
        amount = int(message.text)

        # Обновляем количество воды (прибавляем введённое количество)
        new_amount = current_amount + amount

        # Сохраняем новое значение воды в глобальном контексте FSM
        await state.update_data(water_amount=new_amount)

        # Обновляем данные пользователя в словаре `users`
        if user_id not in users:
            users[user_id] = {"logged_water": 0, "logged_calories": 0, "water_goal": 2000, "calorie_goal": 2000}

        users[user_id]["logged_water"] = new_amount
        await message.answer(f"Вы выпили {amount} мл воды. Общее количество: {new_amount} мл.", reply_markup=buttons)
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное количество воды.")

#Логирование съеденных калорий
@router.callback_query(lambda c: c.data == "log_food")
async def log_food(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите название продукта и его количество в граммах, например: Банан 150")
    await state.set_state(Form.food_calories)

@router.message(Form.food_calories)
async def log_food_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    input_text = message.text

    try:
        # Разделяем название продукта и количество
        product_name, amount = input_text.rsplit(' ', 1)
        amount = int(amount)
    except ValueError:
        await message.answer("Пожалуйста, введите правильный формат: название продукта и количество в граммах.")
        return

    try:
        # Перевод названия продукта на английский
        translated_food = await translate(product_name)
        # Запрос калорий через отдельную функцию
        total_calories = await try_get_food_info(translated_food, amount)

        # Получение текущих данных и обновление калорий
        data = await state.get_data()
        current_calories = data.get('food_calories', 0)
        new_calories = current_calories + total_calories

        # Обновляем контекст и отправляем ответ
        await state.update_data(food_calories=new_calories)
        await message.answer(
            f"Вы получили {total_calories:.2f} ккал из продукта: {product_name}.\n"
            f"Общее количество калорий: {new_calories:.2f} ккал."
        )
        await state.clear()

    except Exception as e:
        await message.answer("Ошибка при обработке запроса. Попробуйте позже.")
        logging.error(f"Ошибка обработки: {e}")

#Логирование сожженных калорий
@router.callback_query(lambda c: c.data == "log_workout")
async def log_workout(callback: CallbackQuery):
    await callback.message.edit_text("Введите тип тренировки и её продолжительность в минутах, например: Бег 30")

@router.callback_query(lambda c: c.data == "check_progress")
async def check_progress(callback: CallbackQuery):
    user = users.get(callback.from_user.id)
    if not user:
        await callback.message.edit_text("Сначала настройте профиль с помощью 'Настроить профиль'.", reply_markup=btnstrt)
        return

    water_goal = user.get("water_goal", 0)
    calorie_goal = user.get("calorie_goal", 0)
    logged_water = user.get("logged_water", 0)
    logged_calories = user.get("logged_calories", 0)
    burning_calories = user.get("burning_calories", 0)

    await callback.message.edit_text(
        f"Ваш прогресс:\n"
        f"Выпито воды: {logged_water}/{water_goal} мл\n"
        f"Потреблено калорий: {logged_calories}/{calorie_goal} ккал",
        f"Сожжено калорий: {burning_calories} ккал",
        reply_markup = buttons
    )