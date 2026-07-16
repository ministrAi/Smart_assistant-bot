
import re
import logging
from services.ai_manager import call_llm

logger = logging.getLogger(__name__)

async def evaluate_answer(question: str, answer: str) -> tuple[bool, str]:
    """
    Оценивает финальный ответ агента перед отправкой пользователю.
    Возвращает (прошёл_ли_проверку, фидбек_для_Observation).
    """
    critic_prompt = [{
        "role": "user",
        "content": (
            f"Вопрос Сэра: {question}\n\n"
            f"Черновой ответ Ориона: {answer}\n\n"
            "Оцени ответ по шкале 1-10, по критериям:\n"
            "1. Точность (соответствует фактам и инструменту)\n"
            "2. Полнота (ответил на все части вопроса)\n"
            "3. Соответствие роли (вежливый, полезный дворецкий, без галлюцинаций)\n\n"
            "Ответь СТРОГО в формате:\n"
            "Score: <число 1-10>\n"
            "Feedback: <что конкретно улучшить, если <7, иначе 'OK'>"
        )
    }]
    try:
        raw = await call_llm(critic_prompt)  # Получаем сырой текст от LLM

        score_match = re.search(r'Score:\s*(\d+)', raw)
        # fail-open: если критик сам сломал формат — не блокируем ответ пользователю
        score = int(score_match.group(1)) if score_match else 10

        feedback_match = re.search(r'Feedback:\s*(.*)', raw, re.DOTALL)
        feedback = feedback_match.group(1).strip() if feedback_match else ""

        passed = score >= 6
        logger.info(f"🧐 Self-Critic: score={score}, passed={passed}")
        return passed, feedback
    except Exception as e:
        logger.error(f"Self-critic упал: {e}")
        return True, "OK"