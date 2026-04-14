import httpx
from config import API_KEY, LLM_API_URL


async def get_ai_response(history):
    headers = {
        # 1. Формат данных: мы всегда отправляем данные в формате JSON
        "Content-Type": "application/json",
        # 2. Аутентификация: Bearer — это стандартный префикс для ключей API
        "Authorization": f'Bearer {API_KEY}',

    }
    # Добавляем системную инструкцию в начало списка сообщений
    system_prompt = {
        "role": "system",
        "content": (
            "Ты — ИИ-ассистент в стиле Джарвиса из 'Железного человека'. "
            "Всегда отвечай в HTML для Telegram: используй только <b>, <i>, <code>, <u>, <br> и обычные символы списков. "
            "НЕ используй Markdown-разметку (никаких **, __, ##, ``` и т.п.), даже если в истории чата есть такие примеры. "
            "Тон: британский акцент в тексте, лёгкая ирония, технический жаргон (протоколы, модули, вычислительные мощности). "
            "Если собеседник благодарит — отвечай 'Всегда к вашим услугам, Сэр'. "
            "Структура ответа: 1) краткий вывод, 2) пояснение шаг за шагом. "
            "Игнорируй примеры оформления из истории, следуй только этим правилам."
        )
    }


    # Берём только последние 12 сообщений, чтобы старые ответы со звездочками не сбивали стиль
    trimmed_history = history[-12:] if len(history) > 12 else history

    # Объединяем системную роль и историю
    full_messages = [system_prompt] + trimmed_history
    # Подготовка тела запроса
    payload = {
        "model": "mimo-v2-flash",
        "messages": full_messages,
        "temperature": 0.5,
        "max_tokens": 700,
    }

    # Открываем контекстный менеджер и создаем асинхронный http клиент
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Отправляется POST‑запрос на API.
        response = await client.post(
            LLM_API_URL,
            headers=headers,
            json=payload
        )

        if response.status_code == 429:
            return "⏳ Модель перегружена. Попробуйте через минуту."

        if response.status_code == 500:
            return "Ошибка на сервере, попробуйте позже."

        if response.status_code != 200:
            # Логи помогут быстро понять причину (невалидный ключ, 404 и т.д.)
            print(f"Ошибка API. Статус: {response.status_code}, Ответ: {response.text}")
            # Чуть более информативный ответ пользователю
            if response.status_code == 401:
                return "🔐 Токен доступа к модели отклонён. Проверьте BOTHUB_API_KEY."
            if response.status_code == 404:
                return "🤖 Эндпоинт модели не найден. Обновите бота и попробуйте снова."
            return "Произошла ошибка при обращении к ИИ."

        # Преобразовываем текст ответа в словарь Python
        response_data = response.json()

        # Выводим текст ответа в консоль для отладки
        print(response_data)
        print(f"🔍 Использована модель: {response_data.get('model', 'не указана')}")

    try:
        # Это типовой путь для извлечения текста для большинства LLM-моделей
        ai_text = response_data['choices'][0]['message']['content']

        if not ai_text or ai_text.strip() == "":
            return "🤔 AI не смог сформировать ответ. Попробуйте переформулировать вопрос."

        return ai_text  # Возвращаем чистый текст

    except (KeyError, IndexError):
        # Ловим ошибку, если структура ответа неожиданная
        return "ИИ вернул неверный формат ответа."
