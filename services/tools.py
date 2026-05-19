
import logging
from datetime import datetime
from services.memory_manager import add_fact_with_check
from services.database import get_facts, get_reflection

logger = logging.getLogger(__name__)

# Сам реестр — просто словарь
_REGISTRY: dict[str, dict] = {}


def register_tool(name: str, description: str, function, parameters: dict = None):
    """Регистрирует инструмент в реестре."""
    _REGISTRY[name] = {
        "name": name,
        "description": description,
        "function": function,
        "parameters": parameters or {}
    }
    logger.info(f"Инструмент зарегистрирован: {name}")


def get_tool(name: str) -> dict | None:
    """Возвращает инструмент по имени или None."""
    return _REGISTRY.get(name)


def get_all_tools() -> dict:
    """Возвращает весь реестр."""
    return _REGISTRY


def get_tools_description() -> str:
    """
    Формирует текстовое описание всех инструментов для системного промпта.
    LLM будет читать именно это.
    """
    lines = []
    for tool in _REGISTRY.values():
        lines.append(f"- {tool['name']}: {tool['description']}")
    return "\n".join(lines)


# ── Атомарные инструменты ──────────────────────────────────────────────

def _get_current_time(timezone: str = "UTC") -> str:
    now = datetime.now()
    return f"Текущее время: {now.strftime('%Y-%m-%d %H:%M:%S')} (timezone: {timezone})"


async def _save_fact(user_id: int, fact: str, importance: str = "medium") -> str:
    await add_fact_with_check(user_id, fact, importance)
    return f"Факт сохранён: '{fact}' (важность: {importance})"


def _get_user_facts(user_id: int) -> str:
    facts = get_facts(user_id)
    if not facts:
        return "Фактов о пользователе не найдено."
    lines = [f"[{f['importance']}] {f['content']}" for f in facts]
    return "Известные факты:\n" + "\n".join(lines)


def _get_reflection(user_id: int) -> str:
    reflection = get_reflection(user_id)
    if not reflection:
        return "Рефлексия о пользователе не найдена."
    line = [f"[{r['timestamp']}] {r['content']}" for r in reflection]
    return "Известные рефлексии:\n" + "\n".join(line)


# ── Регистрация ────────────────────────────────────────────────────────

register_tool(
    name="get_current_time",
    description="Возвращает текущее время. Параметр: timezone (строка, например 'Europe/Moscow').",
    function=_get_current_time,
    parameters={"timezone": "string"}
)

register_tool(
    name="save_fact",
    description="Сохраняет факт о пользователе в долгосрочную память. Параметры: user_id (int), fact (string), importance (low/medium/high).",
    function=_save_fact,
    parameters={"user_id": "int", "fact": "string", "importance": "string"}
)

register_tool(
    name="get_user_facts",
    description="Возвращает все активные факты о пользователе. Параметр: user_id (int)",
    function=_get_user_facts,
    parameters={"user_id": "int"}
)

register_tool(
    name="get_reflection",
    description="Возвращает все рефлексии о пользователе. Параметр: user_id (int)",
    function=_get_reflection,
    parameters={"user_id": "int"}
)