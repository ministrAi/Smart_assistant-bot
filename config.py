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
    "claude-haiku-4-5-20251001": {"input": 131.25, "output": 656.25},
    "deepseek/deepseek-v4-flash": {"input": 16.5, "output": 33.00},
    # "gpt-5.6-luna-2026-07-09": {"input": 23,57, "output": 141,43},
    "gpt-5.6-luna-2026-07-09": {"input": 5.26, "output": 31.55},

}


TOKEN = os.getenv('BOT_TOKEN') # Найдет значение по имени и запомнит в переменную
MAX_ACTIVE_MESSAGES = 70
MAX_ACTIVE_REFLECTION = 25
DATABASE_URL = os.getenv('DATABASE_URL')
# Список Telegram user_id, которым разрешён /hard_delete.
_raw_admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: set[int] = {
    int(x.strip())
    for x in _raw_admins.split(",")
    if x.strip().isdigit()
}

TEST_DB_URL = os.getenv('TEST_DB_URL')

if __name__ == "__main__":
    print(f"Token: {'Found' if TOKEN else 'Not found'}")
    print(f"Admins: {ADMIN_IDS}")
