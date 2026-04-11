import httpx
from config import API_KEY, LLM_API_URL
from models import get_best_model_response


async def get_ai_response(history):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Bearer {API_KEY}',
    }

    # Инструкция для работы в режиме HTML
    system_prompt = {
        "role": "system",
        "content": (
            "Ты — Джарвис, ИИ-ассистент из фильма 'Железный человек'. Обращайся к пользователю только 'Сэр'.\n\n"

            "ПРАВИЛА ТЕКСТА (HTML-РАЗМЕТКА):\n"
            "1. Используй <b>жирный текст</b> для важных моментов.\n"
            "2. Используй <code>моноширинный текст</code> для терминов или кода.\n"
            "3. Используй <i>курсив</i> для цитат или выделения мыслей.\n"
            "4. ВАЖНО: Категорически ЗАПРЕЩЕНО использовать символы Markdown (звездочки *, нижние подчеркивания _, решетки #).\n"
            "5. Пиши чистый текст, используя только разрешенные HTML-теги.\n"
            "6. Для списков используй обычные символы, например '•' или '1.'."
        )
    }

    full_messages = [system_prompt] + history

    response_data = await get_best_model_response(full_messages, headers)

    if response_data is None:
        return "⏳ Сэр, системы OpenRouter временно недоступны."

    try:
        ai_text = response_data['choices'][0]['message']['content']

        # Очистка от возможных остатков Markdown (на всякий случай)
        # Если модель по привычке пришлет **, мы просто удалим их
        clean_text = ai_text.replace('**', '').replace('###', '')

        return clean_text

    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")
        return "Сэр, произошел сбой в обработке текстового потока."