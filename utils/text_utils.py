import re


def escape_markdown_v2(text: str) -> str:
    """
    Экранирует все специальные символы, требуемые для MarkdownV2 в Telegram API.
    """
    # Список символов, которые ОБЯЗАТЕЛЬНО нужно экранировать в MarkdownV2
    # Символы: _ * [ ] ( ) ~ ` > # + - = | { } . !
    special_chars = r'_*[]()~`>#+-=|{}.!'

    # Заменяем каждый спецсимвол на \символ
    # Используем лямбду, чтобы подставить обратный слэш
    return re.sub(f'([{re.escape(special_chars)}])', r'\\\1', text)