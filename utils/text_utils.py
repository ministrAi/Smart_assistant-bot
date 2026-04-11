import re


def escape_markdown_v2(text: str) -> str:
    """
    Экранирует все специальные символы, требуемые для MarkdownV2 в Telegram API.
    """
    print(f"🔧 escape_markdown_v2: входная строка длиной {len(text)}")

    if not isinstance(text, str):
        print(f"⚠️ Ожидалась строка, получено: {type(text)}")
        text = str(text)

    # Список символов, которые ОБЯЗАТЕЛЬНО нужно экранировать в MarkdownV2
    special_chars = r'_*[]()~`>#+-=|{}.!'

    try:
        # Экранируем спецсимволы
        escaped = re.sub(f'([{re.escape(special_chars)}])', r'\\\1', text)
        print(f"✅ Экранирование выполнено успешно, длина результата: {len(escaped)}")
        return escaped
    except Exception as e:
        print(f"❌ Ошибка при экранировании: {e}")
        # В случае ошибки возвращаем оригинал
        return text