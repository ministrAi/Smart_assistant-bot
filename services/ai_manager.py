import httpx
import re


from config import API_KEY, LLM_API_URL, PRICING
import logging
logger = logging.getLogger(__name__)


async def call_llm(messages: list) -> str:
    """
    Чистый транспорт к LLM. Принимает готовый список messages и возвращает текст.
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
        # "model": "deepseek-v3.2",       # Основная модель
        # "model": "gpt-5.6-luna-pro",
        "model": "Claude-Haiku-4.5",
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 1500,
        # "presence_penalty": 0.2,   # Штраф за повторное использование уже затронутых тем
        # "frequency_penalty": 0.3,  # Жёсткий штраф за повторение конкретных слов/токенов
    }

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
            return "⏳ Модель перегружена. Попробуйте через минуту."

        if response.status_code == 500:
            logger.error("Ошибка на сервере, попробуйте позже.")
            return "Ошибка на сервере, попробуйте позже."

        if response.status_code != 200:
            # Логи помогут быстро понять причину (невалидный ключ, 404 и т.д.)
            logger.error(f"Ошибка API. Статус: {response.status_code}, Ответ: {response.text}")
            raise RuntimeError(f"LLM вернул {response.status_code}")

            # Чуть более информативный ответ пользователю
            if response.status_code == 401:
                logger.error("🔐 Токен доступа к модели отклонён. Проверьте BOTHUB_API_KEY.")
                return "🔐 Токен доступа к модели отклонён. Проверьте BOTHUB_API_KEY."
            if response.status_code == 404:
                logger.error("🤖 Эндпоинт модели не найден. Обновите бота и попробуйте снова.")
                return "🤖 Эндпоинт модели не найден. Обновите бота и попробуйте снова."
            logger.error("Произошла ошибка при обращении к ИИ.")
            return "Произошла ошибка при обращении к ИИ."

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
        ai_text = response_data['choices'][0]['message']['content']

        if not ai_text or ai_text.strip() == "":
            logger.error("🤔 AI не смог сформировать ответ. Попробуйте переформулировать вопрос.")
            return "🤔 AI не смог сформировать ответ. Попробуйте переформулировать вопрос."


        # --- БЛОК ПРИНУДИТЕЛЬНОЙ КОРРЕКЦИИ РАЗМЕТКИ (TELEGRAM SAFE) ---
        # 0. Заменяем буквальный текстовый литерал \n (две символа: backslash + n),
        # который модель иногда печатает как текст вместо настоящего перевода строки
        ai_text = ai_text.replace('\\n', '\n')

        # 1. Заменяем ВСЕ варианты <br> (любой регистр, любые пробелы внутри: <br>, <BR>, <br />, <br  />)
        ai_text = re.sub(r'(?i)<br\s*/?>', '\n', ai_text)

        # 2. Очищаем HTML-списки и абзацы (тоже без учета регистра)
        ai_text = re.sub(r'(?i)<ul>|</ul>|<p>|</p>', '', ai_text)
        ai_text = re.sub(r'(?i)<li>', '• ', ai_text)
        ai_text = re.sub(r'(?i)</li>', '\n', ai_text)

        # 3. Принудительно вырезаем Markdown-жирность, которую часто путает модель mimo
        ai_text = ai_text.replace('**', '')

        # 4. Экранируем символы < и >, если они стоят отдельно (защита от поломки HTML)
        ai_text = ai_text.replace(' < ', ' &lt; ').replace(' > ', ' &gt; ')

        logger.info("Отвечаем")
        return ai_text  # Возвращаем чистый текст

    except (KeyError, IndexError):
        # Ловим ошибку, если структура ответа неожиданная
        logger.error("ИИ вернул неверный формат ответа.")
        return "ИИ вернул неверный формат ответа."
