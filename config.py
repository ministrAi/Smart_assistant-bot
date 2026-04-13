import os
from dotenv import load_dotenv  #Импортируем из библиотеки функцию для секретных материалов

load_dotenv()  # Функция автоматически находит и читает .env
FOLDER_KEY = os.getenv('FOLDER_ID')
API_KEY = os.getenv('OPENROUTER_API_KEY')
LLM_API_URL = 'https://openai.bothub.ru/v1/chat/completions'
# 'https://openrouter.ai/api/v1/chat/completions'

TOKEN = os.getenv('BOT_TOKEN') # Найдет значение по имени и запомнит в переменную
MAX_ACTIVE_MESSAGES = 100
DATABASE_URL = os.getenv('DATABASE_URL')
TEST_DB_URL = os.getenv('TEST_DB_URL')

DEFAULT_MODEL = "google/gemma-4-31b-it:free"  # Основная модель

if __name__ == "__main__":
    print(f"Token: {'Found' if TOKEN else 'Not found'}")
