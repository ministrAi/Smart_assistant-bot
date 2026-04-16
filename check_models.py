import httpx
import asyncio
from config import API_KEY


async def check_models():
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    # Получаем список доступных моделей
    async with httpx.AsyncClient() as client:
        response = await client.get(
            # Новый путь BotHub OpenAI API
            "https://bothub.chat/api/v2/openai/v1/models",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ Доступные модели:")
            for model in data.get('data', []):
                print(f"  - {model['id']}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.text)


if __name__ == "__main__":
    asyncio.run(check_models())
