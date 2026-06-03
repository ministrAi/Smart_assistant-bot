# tests/test_parser.py
import pytest
import logging
from services.parser import RobustReActParser, ReActOutput, agent_parser


def test_agent_parser_singleton_instance():
    """Проверяем, что импортированный agent_parser является экземпляром класса RobustReActParser."""
    assert isinstance(agent_parser, RobustReActParser)


def test_react_output_initialization():
    """Проверяем дефолтное состояние структуры данных ReActOutput."""
    output = ReActOutput()
    assert output.plan == ""
    assert output.thought == ""
    assert output.action == ""
    assert output.action_input == {}
    assert output.predict == ""
    assert output.plan_update == ""
    assert output.final_answer == ""
    assert output.raw_output == ""
    assert output.is_final is False


@pytest.mark.parametrize(
    "text, field_name, expected",
    [
        # 1. Базовый сценарий
        ("Thought: Нужно вызвать инструмент.\nAction:", "Thought", "Нужно вызвать инструмент."),

        # 2. Проверка твоих модификаций (Генератор масок вариаций ключа)
        ("Action_Input: {'city': 'MSK'}\nPredict:", "Action Input", "{'city': 'MSK'}"),  # snake_case
        ("Action-Input: {'city': 'MSK'}\nPredict:", "Action Input", "{'city': 'MSK'}"),  # твой дефис!
        ("ActionInput: {'city': 'MSK'}\nPredict:", "Action Input", "{'city': 'MSK'}"),  # слитно
        ("action input: {'city': 'MSK'}\nPredict:", "Action Input", "{'city': 'MSK'}"),  # регистр

        # 3. Азиатские двоеточия и тире (мультиязычные LLM)
        ("Thought： Размышление ИИ\nAction:", "Thought", "Размышление ИИ"),
        ("Thought - Размышление ИИ\nAction:", "Thought", "Размышление ИИ"),

        # 4. Проверка фильтрации мусора (None, null, пустота)
        ("Action: None\nAction Input:", "Action", ""),
        ("Action: null\nAction Input:", "Action", ""),
        ("Action: \nAction Input:", "Action", ""),
    ],
)
def test_extract_field_robustness(text, field_name, expected):
    """Тестируем метод класса _extract_field на устойчивость к синтаксису и мусору."""
    result = RobustReActParser._extract_field(text, field_name)
    assert result == expected


def test_extract_field_lookahead_protection():
    """Проверяем, что Lookahead (опережающая проверка) защищает от наползания блоков."""
    text = (
        "Thought: Я думаю, нужно сделать шаг 1.\n"
        "Затем я сделаю шаг 2 и проверю результат.\n"
        "Action: some_tool"
    )
    result = RobustReActParser._extract_field(text, "Thought")
    expected = "Я думаю, нужно сделать шаг 1.\nЗатем я сделаю шаг 2 и проверю результат."
    assert result == expected


@pytest.mark.parametrize(
    "raw_input, expected_dict",
    [
        # Попытка 1: Валидный чистый JSON
        ('{"city": "Москва", "limit": 5}', {"city": "Москва", "limit": 5}),

        # Попытка 2: JS-like объект (ключи без кавычек)
        ('{city: "Лондон", limit: 2}', {"city": "Лондон", "limit": 2}),

        # Попытка 3: Текстовый формат key=value
        ('city="Париж", limit=1', {"city": "Париж", "limit": "1"}),

        # Попытка 3: Текстовый формат key: value
        ('city: Токио\nlimit: 10', {"city": "Токио", "limit": "10"}),

        # Крайний случай: пустой блок параметров
        ('', {}),
        (None, {}),
    ],
)
def test_parse_action_input_cascade(raw_input, expected_dict):
    """Тестируем 3-х уровневый каскад парсинга аргументов в _parse_action_input."""
    result = RobustReActParser._parse_action_input(raw_input)
    assert result == expected_dict


def test_agent_parser_happy_path():
    """Интеграционный тест синглтона agent_parser на стандартном шаге рассуждения LLM."""
    llm_text = (
        "Plan: Узнать курс валют\n"
        "Thought: Воспользуюсь конвертером.\n"
        "Action: get_currency_rate (актуальный на сегодня)\n"
        "Action Input: {base: 'USD', target: 'RUB'}"
    )

    # Вызываем парсинг через наш глобальный синглтон
    output = agent_parser.parse(llm_text)

    assert output.plan == "Узнать курс валют"
    assert output.thought == "Воспользуюсь конвертером."
    # Проверяем, что регулярка очистила имя инструмента от мусора в скобках
    assert output.action == "get_currency_rate"
    # Проверяем, что параметры успешно распарсились из JS-like формата
    assert output.action_input == {"base": "USD", "target": "RUB"}
    # Агент должен продолжить работу, так как это промежуточный шаг
    assert output.is_final is False
    assert output.raw_output == llm_text.strip()


def test_agent_parser_final_answer():
    """Проверяем поведение синглтона agent_parser, когда LLM выдает финальный ответ."""
    llm_text = (
        "Thought: Задача решена. Вывожу ответ.\n"
        "Final Answer: Курс доллара составляет 92 рубля."
    )

    output = agent_parser.parse(llm_text)

    assert output.thought == "Задача решена. Вывожу ответ."
    assert output.final_answer == "Курс доллара составляет 92 рубля."
    assert output.action == ""
    assert output.action_input == {}
    # Главный флаг остановки цикла должен стать True
    assert output.is_final is True


def test_agent_parser_broken_format(caplog):
    """Проверяем, что при пустом ответе или потере формата парсер логирует ошибки и не падает."""

    # Случай 1: Абсолютно пустая строка от LLM
    with caplog.at_level(logging.WARNING):
        output_empty = agent_parser.parse("   ")
        assert output_empty.is_final is False
        assert "Получен пустой ответ от LLM" in caplog.text

    caplog.clear()

    # Случай 2: LLM прислала текст, проигнорировав формат ReAct
    with caplog.at_level(logging.WARNING):
        output_broken = agent_parser.parse("Привет! Я Джарвис, чем могу помочь?")
        assert output_broken.is_final is False
        assert output_broken.thought == ""
        assert output_broken.final_answer == ""
        assert "Модель сошла с формата: не найдено ни Thought, ни Final Answer." in caplog.text