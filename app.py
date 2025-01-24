import aiohttp
from nutritionix import Nutritionix
from config import API_WEATHER, API_FOOD, API_FOOD_ID, API_SPORT, API_TRANS
import logging
import requests

async def get_weather(city: str, api_key=API_WEATHER):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def get_food_info(food: str, weight: int):
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": API_FOOD_ID,
        "x-app-key": API_FOOD,
        "Content-Type": "application/json"
    }
    body = {"query": food, "timezone": "US/Eastern"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=body) as response:
            if response.status == 200:
                food_info = await response.json()
                if 'foods' in food_info and len(food_info['foods']) > 0:
                    calories_per_100g = food_info['foods'][0].get('nf_calories', 0)
                    calories = (calories_per_100g * weight) / 100
                    return calories
    return 0

async def try_get_food_info(translated_food: str, amount: int) -> float:
    nutritionix = Nutritionix(app_id=API_FOOD_ID, api_key=API_FOOD)
    try:
        # Получение данных о продукте
        food_data = nutritionix.food.get_nutrients(translated_food)
        if not food_data or 'foods' not in food_data:
            raise ValueError("Информация о продукте не найдена.")

        calories_per_100g = food_data['foods'][0].get('nf_calories', 0)
        total_calories = (calories_per_100g * amount) / 100
        return total_calories
    except Exception as e:
        logging.error(f"Ошибка при запросе Nutritionix: {e}")
        raise

def translate(text, target_language='en'):
    url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
    headers = {
        "Authorization": f"Api-Key {API_TRANS}",
        "Content-Type": "application/json"
    }
    params = {
        "targetLanguageCode": target_language,
        "texts": text,
    }
    try:
        response = requests.post(url, headers=headers, json=params)
        response.raise_for_status()
        response_data = response.json()

        if 'translations' in response_data:
            return response_data['translations'][0]['text']
        else:
            raise Exception("Ошибка при переводе текста.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ошибка HTTP запроса: {e}")
    except Exception as e:
        raise Exception(f"Ошибка обработки: {e}")

# Получение данных о тренировках
async def get_workout_info(workout: str):
    url = f"https://api.api-ninjas.com/v1/caloriesburned?activity={workout}"
    headers = {"X-Api-Key": API_SPORT}


    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None