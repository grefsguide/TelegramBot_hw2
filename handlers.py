from aiogram import Router, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app import get_weather, get_food_info, get_workout_info, translate
from states import Form
import logging
import matplotlib.pyplot as plt



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
btns = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Внести выпитую воду", callback_data="log_water")],
                [InlineKeyboardButton(text="Внести съеденную еду", callback_data="log_food")],
                [InlineKeyboardButton(text="Внести тренировку", callback_data="log_workout")],
                [InlineKeyboardButton(text="Графики", callback_data="check_progress_graph")]
            ])

btnstrt = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Настроить профиль", callback_data="set_profile")]])

sex_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Мужчина", callback_data="sex_male")],
    [InlineKeyboardButton(text="Женщина", callback_data="sex_female")]
    ]
)

calorie_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Рассчитать автоматически")],
        [KeyboardButton(text="Ввести вручную")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
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
        await message.reply("Введите существующий город.")

@router.message(Form.city)
async def set_city(message: Message, state: FSMContext):
    city = message.text
    try:
        weather_data = await get_weather(city)
        temperature = weather_data['main']['temp']

        user = users[message.from_user.id]
        user["city"] = city
        user["temperature"] = temperature

        # Рассчитать норму воды
        weight = user["weight"]
        activity = user["activity"]
        water_goal = weight * 30 + (500 * (activity // 30))
        if temperature > 25:
            water_goal += 500
        user["water_goal"] = water_goal

        await message.reply(
            "Как вы хотите установить норму калорий?\n"
            "Вы можете рассчитать автоматически на основе ваших данных или ввести её вручную.",
            reply_markup=calorie_keyboard
        )
        await state.set_state(Form.calorie_choice)
    except Exception as e:
        await message.reply(f"Ошибка при получении данных о погоде: {e}")

@router.message(Form.calorie_choice)
async def set_calorie_choice(message: Message, state: FSMContext):
    choice = message.text.lower()
    user = users[message.from_user.id]

    if "автоматически" in choice:
        weight = user["weight"]
        height = user["height"]
        age = user["age"]
        sex = user["sex"]

        # Расчет калорий
        if sex == 1:
            calorie_goal = round(88.36 + (weight * 13.4) + (height * 5) - (age * 5.7), 1)
        else:
            calorie_goal = round(447.6 + (weight * 9.2) + (height * 3.1) - (age * 4.3), 1)
        user["calorie_goal"] = calorie_goal

        await send_profile_summary(message, user)
        await state.clear()

    elif "ввести вручную" in choice:
        await message.reply("Введите вашу норму калорий (в ккал):")
        await state.set_state(Form.custom_calorie)

    else:
        await message.reply("Пожалуйста, выберите один из доступных вариантов.")

@router.message(Form.custom_calorie)
async def set_custom_calorie(message: Message, state: FSMContext):
    try:
        calorie_goal = float(message.text)
        users[message.from_user.id]["calorie_goal"] = calorie_goal

        await send_profile_summary(message, users[message.from_user.id])
        await state.clear()
    except ValueError:
        await message.reply("Введите корректное число.")

async def send_profile_summary(message: Message, user: dict):
    city = user["city"]
    temperature = user["temperature"]
    water_goal = user["water_goal"]
    calorie_goal = user["calorie_goal"]

    await message.reply(
        f"Профиль настроен!\n"
        f"Город: {city}\n"
        f"Температура: {temperature}°C\n"
        f"Норма воды: {water_goal} мл\n"
        f"Норма калорий: {calorie_goal} ккал.",
        reply_markup=buttons
    )
# Логирование выпитой воды
@router.callback_query(lambda c: c.data == "log_water")
async def log_water(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.logged_water)
    await callback.message.edit_text("Введите количество воды (в мл), которую вы выпили:")

@router.message(Form.logged_water)
async def log_water(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        amount = int(message.text)

        # Инициализируем профиль пользователя, если он отсутствует
        if user_id not in users:
            users[user_id] = {
                "logged_water": 0,
                "logged_calories": 0,
                "water_goal": 2000,
                "calorie_goal": 2000,
            }

        # Убедимся, что ключ 'logged_water' существует
        if "logged_water" not in users[user_id]:
            users[user_id]["logged_water"] = 0

        # Обновляем количество выпитой воды
        users[user_id]["logged_water"] += amount
        logged_water = users[user_id]["logged_water"]
        water_goal = users[user_id]["water_goal"]

        await message.answer(
            f"Вы выпили {amount} мл воды.\n"
            f"Общее количество: {logged_water} мл.\n"
            f"Осталось выпить: {max(0, water_goal - logged_water)} мл.",
            reply_markup=buttons
        )
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
    input_text = message.text.strip()
    user_data = users.get(user_id, {})
    calorie_goal = user_data.get("calorie_goal")
    logged_calories = user_data.get("logged_calories", 0)

    try:
        *product_parts, amount = input_text.split()
        product_name = " ".join(product_parts)
        amount = int(amount)
    except ValueError:
        await message.answer(
            "Пожалуйста, введите правильный формат: название продукта и количество в граммах, например: овсяная каша 200.")
        return

    try:
        translated_food = translate(product_name, target_language='en')
        total_calories = await get_food_info(translated_food, amount)

        # Обновляем количество потребленных калорий
        logged_calories += total_calories
        users[user_id]["logged_calories"] = logged_calories

        await message.answer(
            f"Вы получили {total_calories:.2f} ккал из продукта: {product_name}.\n"
            f"Общее количество полученных калорий: {logged_calories:.2f} ккал.\n"
            f"Осталось: {calorie_goal - logged_calories:.2f} ккал.",
            reply_markup=buttons
        )
        await state.clear()
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")
        logging.error(f"Ошибка при обработке: {e}")


#Логирование сожженных калорий
@router.callback_query(lambda c: c.data == "log_workout")
async def log_workout(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите название упражнения и его длительность в минутах, например: Бег 30")
    await state.set_state(Form.burned_calories)

@router.message(Form.burned_calories)
async def log_burned_calories(message: Message, state: FSMContext):
    user_id = message.from_user.id
    input_text = message.text.strip()

    try:
        # Разделяем строку на все части, предполагая, что последнее слово — это время
        parts = input_text.rsplit(' ', 1)
        if len(parts) != 2:
            raise ValueError("Неверный формат ввода. Пример: Бег 30")

        exercise_name, duration = parts
        duration = int(duration)  # Преобразуем длительность в число минут
        user_weight = users[user_id]['weight']
    except ValueError as e:
        await message.answer(
            "Пожалуйста, введите правильный формат: название упражнения и её длительность в минутах, например: Бег 30.")
        return

    try:
        # Перевод названия упражнения на английский
        translated_exercise = translate(exercise_name, target_language='en')

        # Запрос к Nutritionix API для получения сожженных калорий
        burned_calories = await get_workout_info(translated_exercise, duration, user_weight)

        # Получение текущих данных и обновление сожженных калорий
        current_burned_calories = users[user_id].get("burned_calories", 0)
        new_burned_calories = current_burned_calories + burned_calories

        # Сохраняем данные в FSMContext
        await state.update_data(burned_calories=new_burned_calories)

        # Обновляем данные пользователя в глобальном словаре `users`
        if user_id not in users:
            users[user_id] = {"logged_water": 0, "logged_calories": 0, "burned_calories": 0, "water_goal": 2000,
                              "calorie_goal": 2000}

        users[user_id]["burned_calories"] = new_burned_calories
        total_workout_time = users[user_id].get("workout", 0) + duration
        users[user_id]["workout"] = total_workout_time
        additional_water = (total_workout_time // 20) * 200
        users[user_id]["water_goal"] += additional_water

        # Отправляем пользователю результат
        await message.answer(
            f"Вы сожгли {burned_calories:.2f} ккал за {duration} минут упражнения: {exercise_name}.\n"
            f"Общее количество сожженных калорий: {new_burned_calories:.2f} ккал.\n"
            f"Дополнительно рекомендуется выпить {additional_water} мл воды.\n"
            f"Общее время тренировок: {total_workout_time} минут.",
            reply_markup=buttons
        )
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка обработки: {e}")
        await message.answer("Произошла ошибка при обработке данных. Попробуйте ещё раз.")


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
    burned_calories = user.get("burned_calories", 0)

    await callback.message.edit_text(
        f"Ваш прогресс:\n"
        f"Вода:\n"
        f"- Выпито воды: {logged_water}/{water_goal} мл\n"
        f"- Осталось: {water_goal - logged_water}мл\n"
        f"\nКалории:\n"
        f"- Потреблено калорий: {logged_calories:.1f}/{calorie_goal:.1f} ккал\n" 
        f"- Сожжено калорий: {burned_calories:.1f} ккал\n"
        f"- Баланс: {logged_calories - burned_calories:.1f}",
        reply_markup=btns
    )

# Функция для построения графиков
@router.callback_query(lambda c: c.data == "check_progress_graph")
async def check_progress_graph(callback: types.CallbackQuery):
    user = users.get(callback.from_user.id)
    if not user:
        await callback.message.edit_text("Сначала настройте профиль с помощью 'Настроить профиль'.", reply_markup=btnstrt)
        return

    water_goal = user.get("water_goal", 0)
    logged_water = user.get("logged_water", 0)
    calorie_goal = user.get("calorie_goal", 0)
    logged_calories = user.get("logged_calories", 0)

    fig, axs = plt.subplots(1, 2, figsize=(10, 5))

    axs[0].bar(['Выпито воды'], [logged_water], color='blue', label='Выпито')
    axs[0].bar(['Норма воды'], [water_goal], color='gray', alpha=0.5, label='Норма')
    axs[0].set_title('Прогресс по воде')
    axs[0].legend()

    axs[1].bar(['Потреблено'], [logged_calories], color='green', label='Потреблено')
    axs[1].bar(['Норма калорий'], [calorie_goal], color='gray', alpha=0.5, label='Норма')
    axs[1].set_title('Прогресс по калориям')
    axs[1].legend()

    file_path = "progress_graph.png"
    plt.tight_layout()
    plt.savefig(file_path, format="png")

    photo = FSInputFile(file_path)
    await callback.message.answer_photo(photo=photo, caption="Ваш прогресс по воде и калориям.")

    plt.close(fig)

    # Отправляем кнопки после графика
    await callback.message.answer("Выберите действие:", reply_markup=buttons)

    plt.close(fig)
