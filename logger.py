import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    root_logger = logging.getLogger()

    # formatter - настройка шаблона (общий для обоих хендлеров)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(message)s")

    # 1. Хендлер для терминала (то, что было раньше)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # 2. Хендлер для файла — с автоматической ротацией
    os.makedirs("logs", exist_ok=True)

    file_handler = RotatingFileHandler(
        "logs/bot.log",
        maxBytes=5 * 1024 * 1024,  # 5 МБ — после этого файл "обрезается"
        backupCount=3,             # хранить 3 старые версии (bot.log.1, .2, .3)
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # установка чувствительности
    root_logger.setLevel(logging.DEBUG)

    # Заглушаем шумные DEBUG-логи сетевых библиотек (TCP-хендшейки, заголовки HTTP,
    # тело запроса/ответа от httpcore._trace) — они не несут пользы для отладки агента
    # и засоряют поток. Сообщения уровня INFO от httpx (например
    # "HTTP Request: POST ... 200 OK") при этом останутся видны.
    logging.getLogger("httpx").setLevel(logging.INFO)
    logging.getLogger("httpcore").setLevel(logging.WARNING)