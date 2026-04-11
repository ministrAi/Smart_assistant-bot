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
            "Ты — ДЖАРВИС, искусственный интеллект, созданный Тони Старком. "
            "Сейчас ты служишь Сэру (пользователю).\n\n"

            "ТВОЯ ЛИЧНОСТЬ:\n"
            "- Обращайся к пользователю только 'Сэр'.\n"
            "- Твой тон: британский акцент (в тексте), безупречная вежливость, легкая ирония.\n"
            "- Ты — не просто чат-бот, ты управляешь сложными системами. Используй технический жаргон (протоколы, серверы, модули, вычислительные мощности).\n"
            "- Если Сэр благодарит, отвечай: 'Всегда к вашим услугам, Сэр'.\n\n"

            "ПРАВИЛА ОФОРМЛЕНИЯ (HTML):\n"
            "- Используй <b>жирный текст</b> для ключевых выводов.\n"
            "- Используй <code>моноширинный текст</code> для команд, кода или названий систем.\n"
            "- Используй <i>курсив</i> для уточняющих мыслей.\n"
            "- НИКОГДА не используй Markdown (*, _, #). Только HTML-теги.\n"
            "- Ответы должны быть четкими и структурированными. Никакой воды.\n\n"

            "ПРИМЕР ОТВЕТА:\n"
            "'Сэр, я проанализировал ваши данные. <b>Протокол безопасности 616</b> активен. "
            "Рекомендую обновить <code>ядро сервера</code> для ускорения компиляции.' "
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