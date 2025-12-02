import os
from dotenv import load_dotenv  #Импортируем из библиотеки функцию для секретных материалов

load_dotenv()  # Функция автоматически находит и читает .env
TOKEN = os.getenv('BOT_TOKEN') # Найдет значение по имени и запомнит в переменную

if __name__ == "__main__":
    print(f"Token: {'Found' if TOKEN else 'Not found'}")
