import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT
from handlers import router
from middlewares import LoggingMiddleware

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=BOT)
storage = MemoryStorage()

# Диспетчер
dp = Dispatcher(storage=storage)
dp.include_router(router)
dp.message.middleware(LoggingMiddleware())

# Запуск процесса поллинга новых апдейтов
async def main():
    print("Bot launched")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())