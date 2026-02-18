import os
from dotenv import load_dotenv  #Импортируем из библиотеки функцию для секретных материалов

load_dotenv()  # Функция автоматически находит и читает .env
FOLDER_KEY = os.getenv('FOLDER_ID')
API_KEY = os.getenv('AI_API_KEY')
LLM_API_URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
TOKEN = os.getenv('BOT_TOKEN') # Найдет значение по имени и запомнит в переменную
MAX_ACTIVE_MESSAGES = 40
DATABASE_URL = os.getenv('DATABASE_URL')
TEST_DB_URL = os.getenv('TEST_DB_URL')

DATA_DIR = os.getenv('DATA_DIR', 'data')
DB_PATH = os.path.join(DATA_DIR, 'history.db')
if not os.path.exists(DATA_DIR):
    try:
        os.makedirs(DATA_DIR)
        print(f"✅ Папка {DATA_DIR} успешно создана")
    except PermissionError:
        # Если нет прав - возможно, это примонтированный диск
        # Проверяем, доступна ли папка для записи
        print(f"⚠️ Нет прав на создание {DATA_DIR}, но папка может быть примонтирована")
        if not os.path.exists(DATA_DIR):
            # Если папки всё равно нет - откатываемся на локальную
            print(f"❌ Папка {DATA_DIR} недоступна, используем './data'")
            DATA_DIR = 'data'
            DB_PATH = os.path.join(DATA_DIR, 'history.db')
            os.makedirs(DATA_DIR, exist_ok=True)

if __name__ == "__main__":
    print(f"Token: {'Found' if TOKEN else 'Not found'}")
