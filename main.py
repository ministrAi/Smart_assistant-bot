import asyncio # для асинхронной работы
from aiogram import Bot, Dispatcher # основной фреймворк для Telegram бота
from config import TOKEN
from  handlers.user_handlers import user_router
from services.database import init_db

# Инициализация бота и диспетчера
bot = Bot(token = TOKEN) # подключение к Telegram API
dp = Dispatcher() # диспетчер для обработки входящих сообщений
dp.include_router(user_router) # Подключаем обработчика команд


async def main():

    # Запускаем главную функцию и ОПРОС сервера Telegram на новые сообщения
    init_db() # Создаем таблицу Communication (Message) в начале
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запуск асинхронного приложения
    asyncio.run(main())

