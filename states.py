from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    name = State()
    sex = State()
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()
    workout = State()
    burning_calories = State()
    logget_water = State()
    food_calories = State()