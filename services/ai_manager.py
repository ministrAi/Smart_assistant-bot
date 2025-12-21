import httpx
from config import API_KEY, LLM_API_URL
import json
from openai import OpenAI

async def get_ai_response(prompt_text):

    HEADERS = {
        # 1. Формат данных: мы всегда отправляем данные в формате JSON
        "Content-Type": "application/json",
        # 2. Аутентификация: Bearer — это стандартный префикс для ключей API
        "Authorization": f'Bearer {API_KEY}',
    }
    # Подготовка тела запроса
    PAYLOAD = {
        "model": "yandexgpt-lite",

        "messages": [
            {
                "role": "user",
                "content": prompt_text # <-- Текст, который пришел в функцию
            }
        ],
    }

    #     # 3. Дополнительные настройки (для контроля качества)
    #     # "temperature": 0.7, # Случайность ответа (0.0 - нет, 1.0 - высокая)
    #     "max_tokens": 1024  # Максимальная длина ответа

    # Открываем контекстный менеджер и создаем асинхронный http клиент
    async with httpx.AsyncClient() as client:
        # Отправляется POST‑запрос на API.
        response = await client.post(LLM_API_URL, headers=HEADERS, json=PAYLOAD)

        if response.status_code != 200:
            print(f"Ошибка API. Статус: {response.status_code}, Ответ: {response.text}")
            return "Произошла ошибка при обращении к ИИ."

        if response.status_code == 429:
            return "⏳ Модель перегружена. Попробуйте через минуту."
        
        response_data = response.json()
        print(response_data)

    try:
        # Это типовой путь для большинства LLM-моделей
        ai_text = response_data['choices'][0]['message']['content']
        if not ai_text or ai_text.strip() == "":
            return "🤔 AI не смог сформировать ответ. Попробуйте переформулировать вопрос."
        return ai_text  # Возвращаем чистый текст

    except (KeyError, IndexError):
        # Ловим ошибку, если структура ответа неожиданная
        return "ИИ вернул неверный формат ответа."
