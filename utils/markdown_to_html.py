# utils/markdown_to_html.py
import re


def markdown_to_html(text: str) -> str:
    """
    Конвертирует базовый Markdown в HTML для Telegram
    """
    if not text:
        return text

    # 1. Конвертируем **жирный** в <b>жирный</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

    # 2. Конвертируем *курсив* в <i>курсив</i> (но не трогаем **)
    text = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<i>\1</i>', text)

    # 3. Конвертируем `код` в <code>код</code>
    text = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', text)

    # 4. Конвертируем ```блок кода``` в <pre>блок кода</pre>
    text = re.sub(r'```(\w*)\n(.+?)```', r'<pre>\2</pre>', text, flags=re.DOTALL)

    # 5. Конвертируем [ссылка](url) в <a href="url">ссылка</a>
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)

    # 6. Убираем оставшиеся одиночные * и _
    # (это сломанная Markdown-разметка)

    # 7. Экранируем HTML-теги если они были в оригинальном тексте
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')

    # НО восстанавливаем наши теги (они были экранированы выше)
    text = text.replace('&lt;b&gt;', '<b>')
    text = text.replace('&lt;/b&gt;', '</b>')
    text = text.replace('&lt;i&gt;', '<i>')
    text = text.replace('&lt;/i&gt;', '</i>')
    text = text.replace('&lt;code&gt;', '<code>')
    text = text.replace('&lt;/code&gt;', '</code>')
    text = text.replace('&lt;pre&gt;', '<pre>')
    text = text.replace('&lt;/pre&gt;', '</pre>')
    text = text.replace('&lt;a href=', '<a href=')
    text = text.replace('&lt;/a&gt;', '</a>')

    return text