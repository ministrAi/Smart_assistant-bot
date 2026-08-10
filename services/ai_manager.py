import httpx
from config import API_KEY, LLM_API_URL, PRICING
import logging
logger = logging.getLogger(__name__)


async def call_llm(messages: list, tools: list = None) -> dict:
    """
    Чистый транспорт к LLM. Принимает готовый список messages и возвращает словарь.
    Без системного промпта, без постобработки — только HTTP-запрос.
    """
    headers = {
        # 1. Формат данных: мы всегда отправляем данные в формате JSON
        "Content-Type": "application/json",
        # 2. Аутентификация: Bearer — это стандартный префикс для ключей API
        "Authorization": f'Bearer {API_KEY}',

    }

    # Подготовка тела запроса
    payload = {
        "model": "deepseek-v4-flash",       # Основная модель
        # "model": "gpt-5.6-luna-pro",
        # "model": "claude-haiku-4.5",
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 1500,
        # "presence_penalty": 0.2,   # Штраф за повторное использование уже затронутых тем
        # "frequency_penalty": 0.3,  # Жёсткий штраф за повторение конкретных слов/токенов
    }
    if tools:
        payload["tools"] = tools

    # Открываем контекстный менеджер и создаем асинхронный http клиент
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Отправляется POST‑запрос на API.
        try:
            response = await client.post(
                LLM_API_URL,
                headers=headers,
                json=payload
            )
        except httpx.TimeoutException:
            logger.error("Таймаут запроса к LLM")
            raise  # ← не глотаем ошибку, пробрасываем в agent.py

        if response.status_code == 429:
            logger.error("⏳ Модель перегружена. Попробуйте через минуту.")
            return {"content": "⏳ Модель перегружена. Попробуйте через минуту.", "tool_calls": None}

        if response.status_code == 500:
            logger.error("Ошибка на сервере, попробуйте позже.")
            return {"content":"Ошибка на сервере, попробуйте позже.", "tool_calls": None}

        if response.status_code != 200:
            # Логи помогут быстро понять причину (невалидный ключ, 404 и т.д.)
            logger.error(f"Ошибка API. Статус: {response.status_code}, Ответ: {response.text}")

            if response.status_code == 401:
                logger.error("🔐 Токен доступа к модели отклонён. Проверьте BOTHUB_API_KEY.")
                return {"content": "🔐 Токен доступа к модели отклонён. Проверьте BOTHUB_API_KEY.", "tool_calls": None}

            if response.status_code == 404:
                logger.error("🤖 Эндпоинт модели не найден. Обновите бота и попробуйте снова.")
                return {"content":"🤖 Эндпоинт модели не найден. Обновите бота и попробуйте снова.", "tool_calls": None}

            raise RuntimeError(f"LLM вернул {response.status_code}")



        # Преобразовываем текст ответа в словарь Python
        response_data = response.json()
        # Выводим текст ответа в консоль для отладки
        logger.debug(response_data)
        logger.debug(f"🔍 Использована модель: {response_data.get('model', 'не указана')}")

        usage = response_data.get('usage')
        if usage:
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            model_used = response_data.get('model', payload['model'])
            price = PRICING.get(model_used)

            if price:
                cost_rub = (prompt_tokens / 1_000_000) * price["input"] + (completion_tokens / 1_000_000) * price["output"]
                logger.info(
                    f"💰 Вход: {prompt_tokens} ток. | Выход: {completion_tokens} ток. "
                    f"| Стоимость: ~{cost_rub:.4f}₽ (оценка по тарифу BotHub, возможна погрешность)"
                )
            else:
                logger.warning(
                    f"💰 Вход: {prompt_tokens} ток. | Выход: {completion_tokens} ток. "
                    f"| Модель '{model_used}' отсутствует в config.PRICING — стоимость не оценена"
                )
        else:
            logger.warning("💰 BotHub не вернул поле 'usage' в ответе — учёт токенов невозможен для этого запроса")

    try:
        # Это типовой путь для извлечения текста для большинства LLM-моделей
        message = response_data['choices'][0]['message']

        if not message.get('content') and not message.get('tool_calls'):
            logger.error("🤔 AI не смог сформировать ответ.")
            return {"content": "🤔 AI не смог сформировать ответ...", "tool_calls": None}

        logger.info("Отвечаем")
        return message  # Возвращаем объект message целиком (content + tool_calls)

    except (KeyError, IndexError):
        # Ловим ошибку, если структура ответа неожиданная
        logger.error("ИИ вернул неверный формат ответа.")
        return {"content": "ИИ вернул неверный формат ответа.", "tool_calls": None}
