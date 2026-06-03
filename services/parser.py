import re
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)
# Преобразует «сырой» текст от LLM в структурированный ReAct-шаг

class ReActOutput:
    """Контейнер данных. Структура одного шага ReAct-агента."""
    def __init__(self):
        self.plan: str = ""                     # что планирует агент
        self.thought: str = ""                  # рассуждение
        self.action: str = ""                   # имя инструмента
        self.action_input: Dict[str, Any] = {}  # параметры инструмента (dict)
        self.predict: str = ""                  # что ожидает получить
        self.plan_update: str = ""              # корректировка плана
        self.final_answer: str = ""             # финальный ответ пользователю
        self.raw_output: str = ""               # исходная строка от LLM
        self.cost: float = 0.0
        self.is_final: bool = False             # bool — останавливаем цикл?


class RobustReActParser:
    # Логика парсинга. Берёт строку, заполняет ReActOutput
    # Единый список ключевых слов защищает от "налезания" полей друг на друга
    KEYWORDS = [
        "Plan", "Thought", "Action", "Action Input",
        "Predict", "Plan Update", "Observation", "Final Answer"
    ]

    @classmethod
    def _extract_field(cls, text: str, field_name: str) -> str:
        """Извлекает содержимое конкретного поля из текста LLM,
        останавливаясь перед началом следующего ключевого слова."""
        if not text or not text.strip() or not field_name:
            return ""
            # Генерируем вариации написания поля
        variations = [
            field_name,  # "Action Input"
            field_name.replace(" ", ""),  # "ActionInput"
            field_name.replace(" ", "_"),  # "Action_Input"
            field_name.replace(" ", "-"),
            field_name.lower(),  # "action input"
        ]
        # Подготавливаем lookahead для остановки, превращая список ключевых слов в строку для regex
        lookahead_keys = "|".join(cls.KEYWORDS)
        # Ищем имя поля, двоеточие/тире, и забираем всё до следующего ключевого слова с новой строки или до конца текста
        for var in variations:
            pattern = rf"{re.escape(var)}\s*[:：-]\s*(.*?)(?=\n\s*(?:{lookahead_keys})|\Z)"
            # re.escape() экранирует спецсимволы (на случай "_", "-", etc.)

            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                # Фильтруем пустые/мусорные значения
                if val.lower() in ["none", "null", ""]:
                    return ""
                return val

        return ""
    @classmethod
    def _parse_action_input(cls, text: str) -> Dict[str, Any]:
        """Многоуровневый разбор параметров инструмента. Функция превращает текст параметров от LLM в словварь"""
        if not text:
            return {}

        # Попытка 1: Чистый JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Попытка 2: JSON с пропущенными кавычками у ключей (JS-like объект)
        try:
            cleaned = re.sub(r'(\w+)\s*:', r'"\1":', text)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Попытка 3: Текстовый формат key=value или key: value
        params = {}
        for match in re.finditer(r'(\w+)\s*[:=]\s*["\']?([^"\',\n]+)["\']?', text):
            params[match.group(1)] = match.group(2).strip()

        return params

    def parse(self, text: str) -> ReActOutput:
        output = ReActOutput()
        if not text or not text.strip():
            logger.warning("Получен пустой ответ от LLM")
            return output

        output.raw_output = text.strip()

        # Заполняем текстовые поля через единый безопасный экстрактор
        output.plan = self._extract_field(text, "Plan")
        output.thought = self._extract_field(text, "Thought")
        output.action = self._extract_field(text, "Action")
        output.predict = self._extract_field(text, "Predict")
        output.plan_update = self._extract_field(text, "Plan Update")
        output.final_answer = self._extract_field(text, "Final Answer")

        # Ограничиваем имя инструмента до одного слова (snake_case / подстрока)
        if output.action:
            action_match = re.match(r'([\w_]+)', output.action)
            output.action = action_match.group(1) if action_match else output.action

        # Парсим параметры
        action_input_raw = self._extract_field(text, "Action Input")
        if action_input_raw:
            output.action_input = self._parse_action_input(action_input_raw)

        # Выставляем статус завершения
        output.is_final = bool(output.final_answer)

        if not output.thought and not output.final_answer:
            logger.warning("Модель сошла с формата: не найдено ни Thought, ни Final Answer.")

        return output


# Глобальный синглтон для импорта в сервисах
agent_parser = RobustReActParser()