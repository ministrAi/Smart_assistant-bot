import os
from dotenv import load_dotenv  #Импортируем из библиотеки функцию для секретных материалов

load_dotenv()  # Функция автоматически находит и читает .env

FOLDER_KEY = os.getenv('FOLDER_ID')
API_KEY = os.getenv('BOTHUB_API_KEY') # Для bothub
LLM_API_URL = "https://bothub.chat/api/v2/openai/v1/chat/completions" # Для bothub

# API_KEY = os.getenv('GOOGLE_API_KEY')
# LLM_API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" # для Google AI

PRICING = {
    "deepseek/deepseek-v3.2": {"input": 50.44, "output": 75.00}, # ₽ за 1M токенов (BotHub)
    # "gpt-5.6-luna": {"input": 58.93, "output": 353.57},
    "claude-haiku-4.5": {"input": 131.25, "output": 656.25},
}


TOKEN = os.getenv('BOT_TOKEN') # Найдет значение по имени и запомнит в переменную
MAX_ACTIVE_MESSAGES = 70
MAX_ACTIVE_REFLECTION = 25
DATABASE_URL = os.getenv('DATABASE_URL')
TEST_DB_URL = os.getenv('TEST_DB_URL')

if __name__ == "__main__":
    print(f"Token: {'Found' if TOKEN else 'Not found'}")
