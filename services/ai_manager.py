import httpx
from config import API_KEY, LLM_API_URL, FOLDER_KEY

async def get_ai_response(prompt_text):

    headers = {
        # 1. Формат данных: мы всегда отправляем данные в формате JSON
        "Content-Type": "application/json",
        # 2. Аутентификация: Bearer — это стандартный префикс для ключей API
        "Authorization": f'Bearer {API_KEY}',
    }
    # Подготовка тела запроса
    payload = {
        "modelUri": f"gpt://{FOLDER_KEY}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 1000
        },

        "messages": [
            {
                "role": "user",
                "text": prompt_text
            }
        ]
    }

    #     # 3. Дополнительные настройки (для контроля качества)
    #     # "temperature": 0.7, # Случайность ответа (0.0 - нет, 1.0 - высокая)
    #     "max_tokens": 1024  # Максимальная длина ответа

    # Открываем контекстный менеджер и создаем асинхронный http клиент
    async with httpx.AsyncClient() as client:
        # Отправляется POST‑запрос на API.
        response = await client.post(LLM_API_URL, headers=headers, json=payload)

        if response.status_code == 429:
            return "⏳ Модель перегружена. Попробуйте через минуту."

        if response.status_code != 200:
            print(f"Ошибка API. Статус: {response.status_code}, Ответ: {response.text}")
            return "Произошла ошибка при обращении к ИИ."
        
        response_data = response.json()
        print(response_data)

    try:
        # Это типовой путь для большинства LLM-моделей
        ai_text = response_data['result']['alternatives'][0]['message']['text']
        if not ai_text or ai_text.strip() == "":
            return "🤔 AI не смог сформировать ответ. Попробуйте переформулировать вопрос."
        return ai_text  # Возвращаем чистый текст

    except (KeyError, IndexError):
        # Ловим ошибку, если структура ответа неожиданная
        return "ИИ вернул неверный формат ответа."
