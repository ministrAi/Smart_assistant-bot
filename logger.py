import logging

def setup_logging():
    root_logger = logging.getLogger()

    # handler (обработчик, канал вывода) отвечает за то, куда пойдет информация, в данном случае в терминал
    handler = logging.StreamHandler()

    # formatter - настройка шаблона
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(message)s")
    # склеиваем шаблон и канал вывода
    handler.setFormatter(formatter)

    # активация системы
    root_logger.addHandler(handler)
    # установка чувствительности
    root_logger.setLevel(logging.INFO)
