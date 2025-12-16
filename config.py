import os
from dotenv import load_dotenv  #Импортируем из библиотеки функцию для секретных материалов

load_dotenv()  # Функция автоматически находит и читает .env
API_KEY = os.getenv('AI_API_KEY')
LLM_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
TOKEN = os.getenv('BOT_TOKEN') # Найдет значение по имени и запомнит в переменную

HISTORY_FILE_PATH = 'data/history.json'
DATA_DIR = 'data'

if __name__ == "__main__":
    print(f"Token: {'Found' if TOKEN else 'Not found'}")



