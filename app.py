import aiohttp
from config import API_WEATHER, API_FOOD, API_FOOD_ID, API_TRANS, FOLDER_TRANS
import logging
import requests

# Получение данных о погоде
async def get_weather(city: str, api_key=API_WEATHER):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Получение данных о калориях
async def get_food_info(translated_food: str, amount: int) -> float:
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": API_FOOD_ID,
        "x-app-key": API_FOOD,
        "Content-Type": "application/json"
    }
    body = {
        "query": translated_food,
        "timezone": "US/Eastern"
    }
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()

        if 'foods' not in data or not data['foods']:
            raise ValueError("Информация о продукте не найдена.")

        calories_per_100g = data['foods'][0].get('nf_calories', 0)
        total_calories = (calories_per_100g * amount) / 100
        return total_calories
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка HTTP запроса к Nutritionix: {e}")
        raise
    except Exception as e:
        logging.error(f"Ошибка обработки: {e}")
        raise

# Перевод текста для запросов по еде и тренировкам
def translate(product_name, target_language='en'):
    url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{API_TRANS}"
    }
    body = {
        "targetLanguageCode": target_language,
        "texts": [product_name],
        "folderId": FOLDER_TRANS
    }
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()

        response_data = response.json()
        if 'translations' in response_data:
            return response_data['translations'][0]['text']
        else:
            raise Exception("Ошибка: перевод не найден в ответе.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ошибка HTTP запроса: {e}")
    except Exception as e:
        raise Exception(f"Ошибка обработки: {e}")

# Получение данных о тренировках
async def get_workout_info(exercise_name: str, duration_minutes: int, user_weight: int) -> float:
    url = "https://trackapi.nutritionix.com/v2/natural/exercise"
    headers = {
        "x-app-id": API_FOOD_ID,
        "x-app-key": API_FOOD,
        "Content-Type": "application/json"
    }
    body = {
        "query": f"{exercise_name} {duration_minutes} min",
        "weight_kg": user_weight
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()

        response_data = response.json()

        # Извлекаем данные о сожженных калориях
        if "exercises" in response_data and len(response_data["exercises"]) > 0:
            burned_calories = response_data["exercises"][0].get("nf_calories", 0)
            return burned_calories
        else:
            raise ValueError("Упражнение не найдено в базе Nutritionix.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка HTTP запроса: {e}")
        raise Exception(f"Ошибка HTTP запроса: {e}")
    except Exception as e:
        logging.error(f"Ошибка обработки: {e}")
        raise Exception(f"Ошибка обработки: {e}")


