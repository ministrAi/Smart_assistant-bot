from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from services.database.chat_history import get_conversation_history, save_message, delete_user_messages, get_all_users, getting_statistics
from services.log_streamer import tail_log_file
from pydantic import BaseModel
from datetime import datetime
from services.database import get_facts, get_reflection, deactivate_fact, DatabaseManager
from contextlib import asynccontextmanager



@asynccontextmanager
async def lifespan(app: FastAPI):
    DatabaseManager.init_pool()
    yield
    DatabaseManager._pool.closeall()

app = FastAPI(lifespan=lifespan)



# Получение сообщений
@app.get("/users/{user_id}/messages", summary="Получить историю сообщений")
async def get_user_history(user_id: int, limit: int = 10):
    messages = get_conversation_history(user_id, limit)
    if not messages:
        raise HTTPException(status_code=404, detail="Такого пользователя не существует")
    print(f"Получено сообщений: {len(messages)}")
    return {
        "user_id": user_id,
        "count": len(messages),
        "messages": messages
    }


# Получение фактов о пользователе
@app.get("/users/{user_id}/facts", summary="Получить факты о пользователе")
async def get_user_facts(user_id: int):
    facts = get_facts(user_id)
    if facts is  None:
        facts = []
    print(f"Получено фактов: {len(facts)}")
    return {
        "user_id": user_id,
        "count": len(facts),
        "facts": facts
    }

# Получение рефлексии
@app.get("/users/{user_id}/reflections", summary="Получение списка рефлексий")
async def get_users_reflections(user_id: int):
    reflections = get_reflection(user_id)
    if reflections is None:
        reflections = []
    print(f"Получено рефлексии: {len(reflections)}")
    return {
        "user_id": user_id,
        "count": len(reflections),
        "reflections": reflections
    }


# Деактивация фактов
@app.delete("/users/{user_id}/facts/{fact_id}", summary="Деактивация фактов")
async def  deactivate_user_fact(user_id: int, fact_id: int):
    deactivate_fact(fact_id, user_id)
    return {
        "status": "success",
        "user_id": user_id,
        "fact_id": fact_id
    }


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
    lists_users = get_all_users()
    return {
        "count": len(lists_users),
        "users": lists_users,
    }


# Получение статистики по базе данных
@app.get("/stats", summary="Получить статистику по базе данных")
async def statistics():
    stats = getting_statistics()
    return stats


# Стрим логов в реальном времени (SSE)
@app.get("/logs/stream", summary="Стрим логов бота в реальном времени")
async def stream_logs():
    async def event_generator():
        async for line in tail_log_file():
            yield f"data: {line.rstrip()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Веб-страница просмотра логов
@app.get("/logs", summary="Веб-страница просмотра логов")
async def logs_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Логи Jarvis</title>
        <style>
            body {
                background: #0d0f14;
                color: #e8eaf0;
                font-family: 'JetBrains Mono', monospace;
                font-size: 13px;
                padding: 20px;
                margin: 0;
            }
            #log-container {
                white-space: pre-wrap;
                word-break: break-all;
            }
            .line { padding: 2px 0; border-bottom: 1px solid #1a1e29; }
            .ERROR { color: #f06060; }
            .WARNING { color: #f0a43a; }
            .INFO { color: #8b90a0; }
        </style>
    </head>
    <body>
        <h2>📡 Логи Jarvis (реальное время)</h2>
        <div id="log-container"></div>

        <script>
            const container = document.getElementById('log-container');
            const evtSource = new EventSource('/logs/stream');

            evtSource.onmessage = function(event) {
                const div = document.createElement('div');
                div.className = 'line';

                if (event.data.includes(' - ERROR - ')) {
                    div.classList.add('ERROR');
                } else if (event.data.includes(' - WARNING - ')) {
                    div.classList.add('WARNING');
                } else {
                    div.classList.add('INFO');
                }

                div.textContent = event.data;
                container.appendChild(div);
                window.scrollTo(0, document.body.scrollHeight);
            };

            evtSource.onerror = function() {
                console.log('Соединение с сервером логов потеряно, переподключение...');
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


