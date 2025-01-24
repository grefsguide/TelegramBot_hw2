from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    name = State()
    sex = State()
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()
    water_goal = State()
    calorie_goal = State()
    workout = State()
    burned_calories = State()
    logget_water = State()
    logged_calories = State()
    food_calories = State()
    calorie_choice = State()
    custom_calorie = State()