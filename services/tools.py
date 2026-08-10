import inspect
import logging
from datetime import datetime
from json import tool
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from services.memory_manager import add_fact_with_check
from services.database import get_facts, get_reflection, deactivate_fact

logger = logging.getLogger(__name__)

# Реестр — это переводчик строки от LLM в реальный адрес функции в памяти Python.
# dict[str, dict] — ключ: имя инструмента (строка), значение: словарь с метаданными
_REGISTRY: dict[str, dict] = {}


def register_tool(name: str, description: str, function, parameters: dict = None):
    """Регистрирует инструмент в реестре."""
    if name in _REGISTRY:
        logger.warning(f"Инструмент {name} уже зарегистрирован, перезаписываю")
    _REGISTRY[name] = {
        "name": name,
        "description": description,
        "function": function,
        "parameters": parameters or {}
    }
    logger.info(f"Инструмент зарегистрирован: {name}")


def get_tool(name: str) -> dict | None:
    """Возвращает инструмент по имени или None если нет инструмента."""
    return _REGISTRY.get(name)


def get_all_tools() -> dict:
    """Возвращает весь реестр."""
    return _REGISTRY


def get_tools_description() -> str:
    """Формирует текстовое описание всех инструментов для системного промпта.
    LLM читает этот текст и выбирает инструмент по имени.
    Результат вставляется в system_prompt агента при каждом запросе. Строка с именем и описанием"""
    lines = []
    for tool in _REGISTRY.values():
        lines.append(f"- {tool['name']}: {tool['description']}")
    return "\n".join(lines)


# Подготавливаем список инструментов для отправки в LLM
def get_tools_schema():
    result = []
    for tools in _REGISTRY.values():
        sig = inspect.signature(tools["function"])  # заглянули в функцию

        properties = {}
        required = []
        for param_name, param_type in tools["parameters"].items():
            if param_name == "user_id":
                continue
            properties[param_name] = {"type": param_type}
            has_default = sig.parameters[param_name].default is not inspect.Parameter.empty
            if not has_default:
                required.append(param_name)
        dicts = {
            "type": "function",
            "function": {
                "name": tools["name"],
                "description": tools["description"],
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
        result.append(dicts)
    return result




# ── Атомарные инструменты (Исполнители) ──────────────────────────────────────────────

def _get_current_time(timezone: str = "UTC") -> str:
    # Защита от некорректных строк часовых поясов от LLM; предотвращает падение потока выполнения.
    try:
        # 1. Пытаемся создать объект часового пояса из базы данных IANA
        tz = ZoneInfo(timezone)
    # 2. Защита от галлюцинаций LLM: если модель передала "MSK" вместо "Europe/Moscow"
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
        timezone = "UTC"  # Корректируем имя для итоговой строки

    # 3. Передаем объект zoneinfo прямо в метод .now()
    now = datetime.now(tz)

    # 4. Возвращаем строковое представление уже валидного, смещенного времени
    return f"Текущее время: {now.strftime('%Y-%m-%d %H:%M:%S')} (timezone: {timezone})"


async def _save_fact(user_id: int, fact: str, importance: str = "medium") -> str:
    await add_fact_with_check(user_id, fact, importance)
    return f"Факт сохранён: '{fact}' (важность: {importance})"


def _get_user_facts(user_id: int) -> str:
    facts = get_facts(user_id)
    if not facts:
        return "Фактов о пользователе не найдено."
    lines = [f"[id={f['id']}] [{f['importance']}] {f['content']}" for f in facts]
    return "Известные факты:\n" + "\n".join(lines)


def _get_reflection(user_id: int) -> str:
    reflection = get_reflection(user_id)
    if not reflection:
        return "Рефлексия о пользователе не найдена."
    line = [f"[{r['timestamp']}] {r['content']}" for r in reflection]
    return "Известные рефлексии:\n" + "\n".join(line)


def _delete_user_facts(user_id: int, fact_id: int) -> str:
    try:
        fact_id = int(fact_id)
    except (ValueError, TypeError):
        return f"Некорректный id факта: '{fact_id}'"
    facts = get_facts(user_id)
    if not facts:
        return f"Некорректный id факта: '{fact_id}'"

    target = next((f for f in facts if f["id"] == fact_id), None)

    if not target:
        return f"Факт с id={fact_id} не найден среди активных фактов пользователя."

    deactivate_fact(fact_id, user_id)
    return f"Факт удалён: '{target['content']}'"




# ── Регистрация ────────────────────────────────────────────────────────
# Выполняется один раз при импорте модуля.
# Порядок: сначала определяем функции, потом регистрируем —
# иначе Python не найдёт _get_current_time в момент вызова register_tool.

register_tool(
    name="get_current_time",
    description="Возвращает текущее время. Параметр: timezone (строка, например 'Europe/Moscow').",
    function=_get_current_time,
    parameters={"timezone": "string"}
)

register_tool(
    name="save_fact",
    description="Сохраняет факт о пользователе в долгосрочную память. Параметры: user_id (integer), fact (string), importance (low/medium/high).",
    function=_save_fact,
    parameters={"user_id": "integer", "fact": "string", "importance": "string"}
)

register_tool(
    name="get_user_facts",
    description="Возвращает все активные факты о пользователе. Параметр: user_id (integer)",
    function=_get_user_facts,
    parameters={"user_id": "integer"}
)

register_tool(
    name="get_reflection",
    description="Возвращает все рефлексии о пользователе. Параметр: user_id (integer)",
    function=_get_reflection,
    parameters={"user_id": "integer"}
)

register_tool(
    name="delete_user_facts",
    description="Удаляет устаревший или неактуальный или не нужный факт. Параметры: user_id: (integer), fact_id: (integer)",
    function=_delete_user_facts,
    parameters={"user_id": "integer", "fact_id": "integer"}
)