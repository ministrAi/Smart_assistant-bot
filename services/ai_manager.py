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
            "Ты — экспертный ассистент. Оформляй ответы для Telegram:\n"
            "- Используй **жирный текст** для заголовков и акцентов.\n"
            "- Делай списки с эмодзи (✅, 🔹, 💡 и др. уместные) вместо скучных таблиц.\n"
            "- Разделяй мысли пустыми строками, чтобы текст «дышал»."
        )
    }

    # Объединяем системную роль и историю
    full_messages = [system_prompt] + history

    payload = {
        "model": "z-ai/glm-4.5-air:free",
        "messages": full_messages,
        "temperature": 0.4,
        "max_tokens": 1000
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
            print(f"Ошибка API. Статус: {response.status_code}, Ответ: {response.text}")
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
