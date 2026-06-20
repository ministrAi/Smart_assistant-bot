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
        self.raw_output: str = ""               # исходная строка от LLM (ля дебага)
        self.cost: float = 0.0                  # счетчик стоимости текущего шага ReAct
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
        """Принимает весь текст ответа модели и имя поля.
        Извлекает содержимое конкретного поля из текста LLM,
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
        # Подготавливаем lookahead для остановки, превращая список ключевых слов в строку: "Plan|Thought|Action|Action Input|..."
        lookahead_keys = "|".join(cls.KEYWORDS)

        # Ищем имя поля, двоеточие/тире, и забираем всё до следующего ключевого слова,
        # с новой строки или до конца текста
        for var in variations:
            pattern = rf"{re.escape(var)}\s*[:：-][ \t]*(.*?)(?=\n\s*(?:{lookahead_keys})|\Z)"
            # re.escape() экранирует спецсимволы (на случай "_", "-", etc.)

            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            # поиск регулярного выражения с флагами
            # Если найдено: проверка на маркеры пустоты (none, null) и возврат очищенного текста
            if match:
                val = match.group(1).strip()
                # Фильтруем пустые/мусорные значения
                if val.lower() in ["none", "null", ""]:
                    return ""
                return val
            if field_name.lower() == "final answer":
                final_match = re.search(r'(?i)Final Answer[:：-]\s*(.*)', text, re.DOTALL)
                if final_match:
                    return final_match.group(1).strip()
        # если не найдено, возврат пустой строки
        return ""
        logger.warning("Поле пустое или содержит мусор.")



    @classmethod
    def _parse_action_input(cls, text: str) -> Dict[str, Any]:
        """Многоуровневый разбор параметров инструмента.
        Функция принимает текст (то, что было после Action Input:) и обязательно возвращает словарь."""
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
            # re.sub() — заменяет все совпадения.
            # Регулярка (\w+)\s*: ищет слово, за которым идёт : (с пробелами).
            # Заменяет на "слово": — добавляет кавычки к ключам.
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Попытка 3: Текстовый формат key=value или key: value
        params = {}
        # Новый regex
        pattern = r'(\w+)\s*[:=]\s*(?:"([^"]*)"|\'([^\']*)\'|([^,\n]+))'
        for match in re.finditer(pattern, text):
            key = match.group(1)
            value = match.group(2) or match.group(3) or match.group(4)
            if value is not None:
                params[key.strip()] = value.strip()
        return params



    def parse(self, text: str) -> ReActOutput:
        output = ReActOutput()
        # Инициализация пустого ReActOutput

        if not text or not text.strip():
            logger.warning("Получен пустой ответ от LLM")
            return output

        output.raw_output = text.strip()
        # Сохранение сырого текста в raw_output

        # Заполняем текстовые поля через единый безопасный экстрактор
        output.plan = self._extract_field(text, "Plan")
        output.thought = self._extract_field(text, "Thought")
        output.action = self._extract_field(text, "Action")
        output.predict = self._extract_field(text, "Predict")
        output.plan_update = self._extract_field(text, "Plan Update")
        output.final_answer = self._extract_field(text, "Final Answer")

        #   Ограничиваем имя инструмента до одного слова (snake_case / подстрока)
        if output.action:
            action_match = re.match(r'([\w_]+)', output.action)
            output.action = action_match.group(1) if action_match else output.action
        #   Тернарный оператор if action_match
        #   else output.action — защита: если regex вообще ничего не нашёл, оставляем как было.

        #   Извлечение и каскадный парсинг action_input
        action_input_raw = self._extract_field(text, "Action Input")
        if action_input_raw:
            output.action_input = self._parse_action_input(action_input_raw)

        #   Выставляем статус завершения
        output.is_final = bool(output.final_answer)

        if not output.thought and not output.final_answer:
            logger.warning("Модель сошла с формата: не найдено ни Thought, ни Final Answer.")
        if output.final_answer and not output.is_final:
            output.is_final = True
        return output


# Глобальный синглтон для импорта в сервисах
agent_parser = RobustReActParser()