import asyncio
import os

LOG_FILE_PATH = "logs/bot.log"

async def tail_log_file():
    """Асинхронный генератор: читает лог-файл как `tail -f`.
    Yield'ит новые строки по мере их появления."""

    # Если файла ещё нет (бот не запускался) — ждём его появления
    while not os.path.exists(LOG_FILE_PATH):
        await asyncio.sleep(0.5)

    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        # Переходим в конец файла — нас не интересует история, только новое
        f.seek(0, os.SEEK_END)

        while True:
            line = f.readline()
            if line:
                yield line
            else:
                # Новых строк нет — небольшая пауза, чтобы не грузить CPU постоянным опросом
                await asyncio.sleep(0.5)