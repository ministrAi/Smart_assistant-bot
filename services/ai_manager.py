import httpx
from config import API_KEY, LLM_API_URL


async def get_ai_response(history):

    headers = {
        # 1. Формат данных: мы всегда отправляем данные в формате JSON
        "Content-Type": "application/json",
        # 2. Аутентификация: Bearer — это стандартный префикс для ключей API
        "Authorization": f'Bearer {API_KEY}',
    }
    # Подготовка тела запроса
    payload = {
        "model": "minimax-m2.7",
        "messages": history,
        "temperature": 0.5,
        "max_tokens": 700,
    }

    # Открываем контекстный менеджер и создаем асинхронный http клиент
    async with httpx.AsyncClient() as client:
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

    try:
        # Это типовой путь для извлечения текста для большинства LLM-моделей
        ai_text = response_data['choices'][0]['message']['content']

        if not ai_text or ai_text.strip() == "":
            return "🤔 AI не смог сформировать ответ. Попробуйте переформулировать вопрос."

        return ai_text  # Возвращаем чистый текст

    except (KeyError, IndexError):
        # Ловим ошибку, если структура ответа неожиданная
        return "ИИ вернул неверный формат ответа."
