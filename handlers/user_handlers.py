from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import F
from datetime import datetime
from services.ai_manager import get_ai_response
from services.database import save_message
from services.database import get_conversation_history, delete_user_messages

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


@user_router.message(Command("clear"))
async def cmd_clear(message: Message):
    user_id = message.from_user.id

    total_deleted = delete_user_messages(user_id)

    if total_deleted > 0:
        # Если в базе были записи с is_active = 1
        await message.answer(f"🧹 История очищена! Скрыто записей: {total_deleted}")
    else:
        # Если записей не было или у всех уже стоит is_active = 0
        await message.answer("Ваша история и так пуста или уже была очищена! ✨")

@user_router.message(F.text)
async def process_echo(message: Message):
    # Сохраняем сообщение пользователя
    save_message(
        user_id=message.from_user.id,
        role='user',
        text=message.text,
        timestamp=datetime.now().isoformat()
    )

    #  Получаем историю сообщений пользователя по id
    history = get_conversation_history(message.from_user.id)
    # Отправляем историю диалога в YaGPT и сохраняем ответ в переменную
    gpt_text = await get_ai_response(history)

    #  Сохраняем ответ AI
    save_message(
        user_id=message.from_user.id,
        role='assistant',
        text=gpt_text,
        timestamp=datetime.now().isoformat()
    )
    # Отправка ответа пользователю
    await message.answer(gpt_text, parse_mode="Markdown")


