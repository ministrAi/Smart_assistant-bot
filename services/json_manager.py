# import json
#
#
# def load_history(file_path):
#     """
#     Вернуть список старых сообщений, даже если файл пуст или не существует.
#     """
#     try:
#         with open(file_path, 'r', encoding='utf-8') as h:
#             return json.load(h)  # Читает содержимое файла и преобразует его из формата JSON в список Python
#
#     except FileNotFoundError:
#         return []
#
#     except json.JSONDecodeError:
#         return []
#
#
# def save_history(file_path, new_record):
#     """
#     Функция сохранения истории.
#     """
#     current_history = load_history(file_path)
#     current_history.append(new_record)
#
#     with open(file_path, 'w', encoding='utf-8') as f:
#         json.dump(current_history, f, indent=4, ensure_ascii=False)
