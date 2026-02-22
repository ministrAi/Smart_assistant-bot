import os
from dotenv import load_dotenv  #Импортируем из библиотеки функцию для секретных материалов

load_dotenv()  # Функция автоматически находит и читает .env
FOLDER_KEY = os.getenv('FOLDER_ID')
API_KEY = os.getenv('AI_API_KEY')
LLM_API_URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
TOKEN = os.getenv('BOT_TOKEN') # Найдет значение по имени и запомнит в переменную
MAX_ACTIVE_MESSAGES = 100
DATABASE_URL = os.getenv('DATABASE_URL')
TEST_DB_URL = os.getenv('TEST_DB_URL')

if __name__ == "__main__":
    print(f"Token: {'Found' if TOKEN else 'Not found'}")
