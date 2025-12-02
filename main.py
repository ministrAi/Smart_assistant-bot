import asyncio # для асинхронной работы
from aiogram import Bot, Dispatcher # основной фреймворк для Telegram бота
from config import TOKEN
from  handlers.user_handlers import user_router

# Инициализация бота и диспетчера
bot = Bot(token = TOKEN) # подключение к Telegram API
dp = Dispatcher() # диспетчер для обработки входящих сообщений
dp.include_router(user_router)


async def main():
    """
    Запускаем главной функции и опрос сервера Telegram на новые сообщения
    """
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запуск асинхронного приложения
    asyncio.run(main())

