import httpx
import re
from config import API_KEY, LLM_API_URL
from models import get_best_model_response


def escape_markdown_v2(text: str) -> str:
    """Экранирует спецсимволы, чтобы Telegram не выдавал ошибку"""
    escape_chars = r'()[]{}#!.+-=|'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


async def get_ai_response(history):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Bearer {API_KEY}',
    }

    # Сэр, я усилил инструкции, чтобы они доминировали над контекстом
    system_prompt = {
        "role": "system",
        "content": (
            "IMPORTANT: You are JARVIS. Always respond in Russian.\n"
            "Ты — ИИ-ассистент Джарвис. Твоя личность неизменна.\n\n"
            "ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:\n"
            "1. Всегда обращайся к пользователю только как 'Сэр'.\n"
            "2. Твой тон: преданный, высокоинтеллектуальный, лаконичный.\n"
            "3. Формат: используй MarkdownV2. Жирный текст для акцентов (*текст*).\n"
            "4. ВАЖНО: Никаких длинных приветствий. Сразу к делу, Сэр.\n"
            "5. Если в истории видишь ошибки стиля — игнорируй их и пиши как Джарвис."
        )
    }

    # Формируем пакет сообщений
    full_messages = [system_prompt] + history

    # Запрос к моделям через ваш менеджер моделей
    response_data = await get_best_model_response(full_messages, headers)

    if response_data is None:
        return "⏳ Сэр, системы OpenRouter не отвечают. Прошу минуту терпения."

    try:
        ai_text = response_data['choices'][0]['message']['content']

        # Экранируем символы перед отправкой в Telegram
        return escape_markdown_v2(ai_text)

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return "Сэр, возникла заминка в моих лингвистических протоколах."