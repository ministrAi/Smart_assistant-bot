import os
from dotenv import load_dotenv  #Импортируем из библиотеки функцию для секретных материалов

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

load_dotenv()  # Функция автоматически находит и читает .env
FOLDER_KEY = os.getenv('FOLDER_ID')
API_KEY = os.getenv('BOTHUB_API_KEY')
# BotHub keeps OpenAI‑совместимый API по новому пути /api/v2/openai/v1
# Старый поддомен openai.bothub.chat перестал отвечать 200 и возвращает 404,
# из‑за чего бот печатал "Произошла ошибка при обращении к ИИ."
LLM_API_URL = "https://bothub.chat/api/v2/openai/v1/chat/completions"

TOKEN = os.getenv('BOT_TOKEN') # Найдет значение по имени и запомнит в переменную
MAX_ACTIVE_MESSAGES = 40

# По умолчанию используем локальный SQLite-файл. Если нужен Postgres — укажите в .env
DEFAULT_DB_PATH = os.path.join(DATA_DIR, "history.db")
DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{DEFAULT_DB_PATH}")
TEST_DB_URL = os.getenv('TEST_DB_URL', f"sqlite:///{os.path.join(DATA_DIR, 'test_history.db')}")

if __name__ == "__main__":
    print(f"Token: {'Found' if TOKEN else 'Not found'}")
