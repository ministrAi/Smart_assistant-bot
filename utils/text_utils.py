import re


def escape_markdown_v2(text: str) -> str:
    """
    Экранирует специальные символы Telegram MarkdownV2,
    НО сохраняет валидную Markdown-разметку (*жирный*, _курсив_ и т.д.)
    """
    print(f"🔧 escape_markdown_v2: входная строка длиной {len(text)}")

    if not isinstance(text, str):
        print(f"⚠️ Ожидалась строка, получено: {type(text)}")
        text = str(text)

    # Символы, которые нужно экранировать ТОЛЬКО если они не часть Markdown-разметки
    # Экранируем: . ! ? - ( ) [ ] { }
    special_chars_map = {
        '.': '\\.',
        '!': '\\!',
        '?': '\\?',
        '-': '\\-',
        '(': '\\(',
        ')': '\\)',
        '[': '\\[',
        ']': '\\]',
        '{': '\\{',
        '}': '\\}',
        '=': '\\=',
        '+': '\\+',
        '_': '\\_',
        '*': '\\*',
        '~': '\\~',
        '>': '\\>',
        '#': '\\#',
        '|': '\\|',
    }

    # НЕ экранируем символы, которые являются частью валидной Markdown-разметки:
    # **жирный**, *курсив*, __жирный__, _курсив_, `код`, ```блок кода```

    def should_escape(match):
        char = match.group(0)
        pos = match.start()

        # Проверяем контекст вокруг символа
        before = text[max(0, pos - 1):pos]
        after = text[pos + 1:pos + 2] if pos + 1 < len(text) else ''

        # Если это часть Markdown-разметки - не экранируем
        if char == '*' and (before == '*' or after == '*'):
            return char  # Это **жирный**, не экранируем
        if char == '_' and (before == '_' or after == '_'):
            return char  # Это __жирный__ или _курсив_, не экранируем
        if char == '`' and (after == '`' or before == '`'):
            return char  # Это `код`, не экранируем

        # В остальных случаях экранируем
        return special_chars_map.get(char, char)

    try:
        # Экранируем только одиночные специальные символы
        escaped = re.sub(r'[.!?\-()\[\]{}"\'=+#_*~>#|]', should_escape, text)
        print(f"✅ Экранирование выполнено успешно, длина результата: {len(escaped)}")
        return escaped
    except Exception as e:
        print(f"❌ Ошибка при экранировании: {e}")
        return text