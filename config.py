import os
from dotenv import load_dotenv

load_dotenv()

BOT = os.getenv("BOT_TOKEN")
API_WEATHER = os.getenv("API_TOKEN_WEATHER")
API_FOOD = os.getenv("API_TOKEN_FOOD")
API_FOOD_ID = os.getenv("API_TOKEN_FOOD_ID")
API_TRANS = os.getenv("API_TOKEN_TRANS")
FOLDER_TRANS = os.getenv("FOLDER_TRANS")