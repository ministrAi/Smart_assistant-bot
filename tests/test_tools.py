import pytest
from services.tools import get_tools_description, register_tool
from services.tools import get_tool, get_all_tools


# Проверка вызова функции инструмента
def test_get_current_time_executes():
    tool = get_tool("get_current_time")
    result = tool["function"](timezone="UTC")
    assert "Текущее время" in result


def test_register_tool_adds_to_registry():
    """
    Проверяем, что после регистрации инструмент появляется в реестре.
    Это основа паттерна Registry — инструмент должен
    сохраняться и быть доступным по имени.
    """

    # Регистрируем тестовый инструмент
    def dummy_function():
        return "test result"

    register_tool(
        name="test_tool",
        description="Тестовый инструмент",
        function=dummy_function,
        parameters={"arg1": "string"}
    )

    # Проверяем, что инструмент добавился в реестр
    tool = get_tool("test_tool")

    assert tool is not None, "Инструмент должен быть в реестре"
    assert tool["name"] == "test_tool"
    assert tool["description"] == "Тестовый инструмент"
    assert tool["function"] is dummy_function
    assert tool["parameters"] == {"arg1": "string"}


def test_get_tool_returns_existing_tool():
    """
    Проверяем, что можем получить ранее зарегистрированный инструмент.
    Инструмент get_current_time уже зарегистрирован при импорте tools.py,
    поэтому просто проверяем его получение.
    """
    tool = get_tool("get_current_time")

    assert tool is not None, "Стандартный инструмент должен существовать"
    assert "function" in tool, "У инструмента должна быть функция"
    assert "description" in tool, "У инструмента должно быть описание"


def test_get_tool_returns_none_for_missing():
    """
    Проверяем, что при запросе несуществующего инструмента возвращается None.
    Почему важно: агент должен корректно обрабатывать ситуацию,
    когда запрошенный инструмент не найден — не падать, а вернуть None.
    """
    tool = get_tool("non_existent_tool_12345")

    assert tool is None, "Несуществующий инструмент должен возвращать None"


def test_get_all_tools_returns_dict():
    """
    Проверяем, что get_all_tools возвращает словарь.
    Зачем: агент может захотеть получить список всех доступных
    инструментов для динамического выбора.
    """
    all_tools = get_all_tools()

    assert isinstance(all_tools, dict), "Реестр должен быть словарём"
    assert len(all_tools) > 0, "Реестр не должен быть пустым"
    assert "get_current_time" in all_tools, "Стандартные инструменты должны быть"



def test_get_tools_description_format():
    """
    Проверяем, что описание формируется в правильном формате.
    Этот текст попадает в системный промпт LLM, чтобы он знал
    какие инструменты доступны. Формат: "- имя: описание"
    """
    description = get_tools_description()

    assert isinstance(description, str), "Описание должно быть строкой"
    assert "get_current_time" in description, "Должно содержать имя инструмента"
    assert "save_fact" in description, "Должно содержать имя инструмента"
    # Проверяем формат: "- имя: описание"
    assert "- " in description, "Должен быть маркированный список"