from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import F
from datetime import datetime
from services.json_manager import save_history

user_router = Router()


@user_router.message(Command("start"))
async def process_start(message: Message):
    """
    Обработчик команды /start.
    Отвечает пользователю, подтверждая работоспособность системы.
    """
    await message.answer('Система исправна! Добро пожаловать')

@user_router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обработчик команды /help.
    Отвечает пользователю, подсказывая доступные команды.
    """
    await message.answer('"Я - твой умный ассистент. Доступные команды: /start, /help."')

@user_router.message(F.text)
async def process_echo(message: Message):
    new_record = {
        'user_id': message.from_user.id,
        'text': message.text,
        'timestamp': datetime.now().isoformat(),
    }

    JSON_FILE_PATH = 'data/history.json'
    save_history(JSON_FILE_PATH, new_record)

    user_text = message.text
    await message.answer(f'Слышу тебя: {user_text}')
    print(message.text)
