from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import F
from datetime import datetime
from services.ai_manager import get_ai_response
from services.database import save_message
from services.database import get_conversation_history, delete_user_messages
from utils.text_utils import escape_markdown_v2

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
        await message.answer(f"🧹 История очищена! Скрыто записей: {total_deleted}")
    else:
        await message.answer("Ваша история и так пуста или уже была очищена! ✨")


@user_router.message(F.text)
async def process_echo(message: Message):
    user_id = message.from_user.id

    try:
        # 1. Сохраняем сообщение пользователя
        print(f"💾 Сохраняю сообщение от user={user_id}")
        save_message(
            user_id=user_id,
            role='user',
            text=message.text,
            timestamp=datetime.now().isoformat()
        )
        print("✅ Сообщение пользователя сохранено")

        # 2. Получаем историю
        print("📚 Получаю историю диалога...")
        history = get_conversation_history(user_id)
        print(f"📊 Получено {len(history)} сообщений из истории")

        # 3. Запрос к AI
        print("🤖 Отправляю запрос к AI...")
        gpt_text = await get_ai_response(history)
        print(f"📝 Получен ответ от AI длиной {len(gpt_text) if gpt_text else 0} символов")
        print(f"📝 Текст ответа: {gpt_text[:100] if gpt_text else 'None'}...")

        # 4. Отправка ответа
        try:
            print("🔧 Экранирую текст для MarkdownV2...")
            safe_text = escape_markdown_v2(gpt_text)
            print(f"📤 Отправляю ответ пользователю (с форматированием)...")

            await message.answer(safe_text, parse_mode="MarkdownV2")
            print("✅ Ответ отправлен успешно")

        except Exception as markdown_error:
            print(f"⚠️ Ошибка Markdown: {markdown_error}")
            print("📤 Отправляю ответ без форматирования...")
            await message.answer(gpt_text)
            print("✅ Ответ отправлен (без форматирования)")

        # 5. Сохраняем ответ AI
        print("💾 Сохраняю ответ AI в БД...")
        save_message(
            user_id=user_id,
            role='assistant',
            text=gpt_text,
            timestamp=datetime.now().isoformat()
        )
        print("✅ Ответ AI сохранен")

    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

        # Отправляем сообщение об ошибке
        await message.answer("Произошла внутренняя ошибка. Пожалуйста, попробуйте позже.")


