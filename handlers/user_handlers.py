from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import F
from datetime import datetime
# from services.json_manager import save_history
# from config import HISTORY_FILE_PATH
from services.ai_manager import get_ai_response
from services.database import save_message

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
    save_message(user_id=message.from_user.id, role='user', text=message.text, timestamp=datetime.now().isoformat()
    )

    gpt_text = await get_ai_response(message.text)
    save_message(gpt_text=message.from_user.id, role='assistant', text=message.text, timestamp=datetime.now().isoformat())
    await message.answer(gpt_text)

