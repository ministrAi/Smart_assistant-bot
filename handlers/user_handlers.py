import re
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import F
from datetime import datetime
from services.agent import run_agent
from services.database import save_message, delete_user_messages, hard_reset_communications
from services.database import get_facts, get_reflection
from services.task_registry import register_task, unregister_task, cancel_task
import asyncio

user_router = Router()

import logging
logger = logging.getLogger(__name__)


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

@user_router.message(Command("hard_delete"))
async def admin_clear(message: Message):
    hard_reset_communications()
    await message.answer("<b>Протоколы очищены.</b> Система перезапущена с нулевым индексом.", parse_mode="HTML")


@user_router.message(Command("memory"))
async def cmd_memory(message: Message):
    user_id = message.from_user.id
    facts = get_facts(user_id)  # нужно импортировать
    reflections = get_reflection(user_id)

    response = "<b>🧠 Память Сэра:</b>\n\n"

    if facts:
        response += "<b>Факты:</b>\n"
        for f in facts[:5]:
            response += f"• [{f['importance']}] {f['content']}\n"
    else:
        response += "Фактов пока нет.\n"

    if reflections:
        response += "\n<b>Рефлексии:</b>\n"
        for r in reflections[-3:]:
            response += f"• {r['timestamp'][:10]}: {r['content'][:150]}...\n"

    await message.answer(response, parse_mode="HTML")


@user_router.message(F.text)
async def process_echo(message: Message):
    user_id = message.from_user.id

    # Показываем что бот печатает
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # 1. Сохраняем сообщение пользователя
        save_message(
            user_id=user_id,
            role='user',
            text=message.text,
            timestamp=datetime.now().isoformat()
        )
        logger.debug("✅ Сообщение пользователя сохранено")

        # # 2. Получаем историю
        # logger.info("📚 Получаю историю диалога...")
        # history = get_conversation_history(user_id)
        # logger.debug(f"📊 Получено {len(history)} сообщений из истории")

        # 3. Запрос к AI — через Task, чтобы можно было отменить извне
        logger.info("🤖 Отправляю запрос к AI...")
        task = asyncio.create_task(run_agent(user_id, message.text))
        register_task(user_id, task)
        try:
            gpt_text = await task
        except asyncio.CancelledError:
            logger.info(f"🛑 Задача отменена пользователем: user_id={user_id}")
            await message.answer(
                "<b>Задача остановлена, Сэр.</b> Протокол прерван по вашей команде.",
                parse_mode="HTML"
            )
            return
        finally:
            unregister_task(user_id)

        # 4. Отправка ответа
        try:
            # Теперь используем HTML
            await message.answer(gpt_text, parse_mode="HTML")
            logger.debug("✅ Ответ отправлен успешно (HTML)")

        except Exception as html_error:
            logger.warning(f"⚠️ Ошибка HTML разметки: {html_error}")
            # Если теги все же сломаны, чистим их и отправляем как текст

            clean_text = re.sub('<[^<]+?>', '', gpt_text)
            await message.answer(clean_text)
            logger.debug("✅ Ответ отправлен (очищенный от тегов)")

        # 5. Сохраняем ответ AI
        logger.info("💾 Сохраняю ответ AI в БД...")
        save_message(
            user_id=user_id,
            role='assistant',
            text=gpt_text,
            timestamp=datetime.now().isoformat()
        )
        logger.debug("✅ Ответ AI сохранен")

    except Exception as e:
        logger.exception(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {type(e).__name__}: {e}")

        # Отправляем сообщение об ошибке
        await message.answer(
            "<b>Произошла внутренняя ошибка.</b> Пожалуйста, попробуйте позже.",
            parse_mode="HTML"
        )

@user_router.message(Command("stop"))
async def cmd_stop(message: Message):
    user_id = message.from_user.id
    stopped = cancel_task(user_id)

    if stopped:
        await message.answer(
            "<b>Принято.</b> Отменяю текущий протокол...",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "<i>Активных задач не найдено.</i> Я уже свободен, Сэр.",
            parse_mode="HTML"
        )