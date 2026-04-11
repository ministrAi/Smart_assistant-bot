# models.py - отдельный файл для управления моделями
import httpx
from config import API_KEY, LLM_API_URL

# Список моделей в порядке приоритета
MODEL_LIST = [
    "nvidia/nemotron-3-nano-30b-a3b:free",  # 1. Быстрая
    "google/gemma-4-31b-it:free",  # 2. Умная (у вас уже работает)
    "qwen/qwen3-6b-plus:free",  # 3. Баланс
    "meta-llama/llama-3.2-3b-instruct:free",  # 4. Стабильная
    "google/gemini-2.0-flash-lite-preview-02-05:free"  # 5. Резерв
]


async def try_single_model(model_id, full_messages, headers):
    """Пробует одну модель"""
    payload = {
        "model": model_id,
        "messages": full_messages,
        "temperature": 0.4,
        "max_tokens": 1000
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
        response = await client.post(LLM_API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print(f"⚠️ Модель {model_id} перегружена, пробую следующую...")
            return None
        else:
            print(f"❌ Ошибка {response.status_code} от {model_id}")
            return None


async def get_best_model_response(full_messages, headers):
    """Перебирает модели пока не найдёт работающую"""
    for model_id in MODEL_LIST:
        result = await try_single_model(model_id, full_messages, headers)
        if result:
            print(f"✅ Использую модель: {model_id}")
            return result

    # Если ни одна не сработала
    print("❌ Все модели недоступны")
    return None