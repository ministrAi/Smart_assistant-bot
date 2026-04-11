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
    """
    await message.answer(
        '<b>Система исправна!</b> Добро пожаловать, Сэр.',
        parse_mode="HTML"
    )


@user_router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обработчик команды /help.
    """
    await message.answer(
        '<b>Я - твой умный ассистент.</b>\n\n'
        '<u>Доступные команды:</u>\n'
        '/start - Проверка системы\n'
        '/help - Помощь\n'
        '/clear - Очистить историю диалога',
        parse_mode="HTML"
    )


@user_router.message(Command("clear"))
async def cmd_clear(message: Message):
    user_id = message.from_user.id
    total_deleted = delete_user_messages(user_id)

    if total_deleted > 0:
        await message.answer(
            f"🧹 <b>История очищена!</b> Скрыто записей: {total_deleted}",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "<i>Ваша история и так пуста или уже была очищена!</i> ✨",
            parse_mode="HTML"
        )


@user_router.message(F.text)
async def process_echo(message: Message):
    user_id = message.from_user.id

    # Показываем что бот печатает
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

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

        # 4. Отправка ответа с HTML разметкой
        try:
            await message.answer(gpt_text, parse_mode="HTML")
            print("✅ Ответ отправлен успешно (HTML)")

        except Exception as html_error:
            print(f"⚠️ Ошибка HTML разметки: {html_error}")
            # Если HTML сломан - отправляем чистый текст
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
        await message.answer(
            "<b>Произошла внутренняя ошибка.</b> Пожалуйста, попробуйте позже.",
            parse_mode="HTML"
        )