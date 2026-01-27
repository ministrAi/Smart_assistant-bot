from fastapi import FastAPI
from services.database import get_conversation_history, save_message, delete_user_messages, get_all_users, getting_statistics
from pydantic import BaseModel
from fastapi import HTTPException
from datetime import datetime


app = FastAPI()

# Получение сообщений
# Декоратор, который регистрирует эндпоинт
@app.get("/users/{user_id}/messages", summary="Получить историю сообщений")
async def get_user_history(user_id: int, limit: int = 10):

    messages = get_conversation_history(user_id, limit)

    # Проверяем что смс вообще есть
    if not messages:
        raise HTTPException(status_code=404, detail= "Такого пользователя не существует")

    print(f"Получено сообщений: {len(messages)}")

    return {
        "user_id": user_id,
        "count": len(messages),
        "messages": messages
    } # http://127.0.0.1:8000/users/1067369536/messages?limit=3



# Сохранение сообщений
class MessageCreate(BaseModel):
    user_id: int
    role: str
    text: str
@app.post("/messages", summary="Создать новое сообщение в БД")
async def create_message(message: MessageCreate):
    current_time = datetime.now()
    save_message(
        user_id=message.user_id,
        role=message.role,
        text=message.text,
        timestamp=current_time
    )

    return {
        "status": "success",
        "message": "Сообщение сохранено"
    }



# Удаление сообщений из БД
@app.delete("/users/{user_id}/messages", summary="Удалить сообщения пользователя")
async def delete_messages(user_id: int):
    deleted_count = delete_user_messages(user_id)

    return {
        "status": "success",
        "deleted_count": deleted_count
    }



# Получение списка пользователей
@app.get("/users", summary="Получить список всех пользователей")
async def list_users():
    lists_users = get_all_users(user_id=list_users)
    return {
        "count": len(lists_users),
        "users": lists_users,
    }



@app.get("/stats", summary="Получить статистику по базе данных")
async def statistics():
    stats = getting_statistics()
    return stats


# Привет









