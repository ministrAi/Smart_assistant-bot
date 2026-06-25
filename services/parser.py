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
        # с новой строки, без неё (слипшийся текст без \n), или до конца текста
        for var in variations:
            pattern = rf"{re.escape(var)}\s*[:：-]\s*(.*?)(?=\s*(?:{lookahead_keys})\s*[:：-]|\Z)"
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
        pattern = r'(\w+)\s*[:=]\s*(?:"([^"]*)"|\'([^\']*)\'|([^,]+))'
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

        # Если регулярки не нашли ни одного ключевого слова,
        # но модель прислала содержательный связный текст:
        if not output.action and not output.final_answer and text.strip():
            raw_text = text.strip()

            # ЗАЩИТА ОТ ЗАЦИКЛИВАНИЯ (Repetition Loop Prevention)
            # Ищем, если одно и то же слово повторяется 4 или более раз подряд через пробел
            if re.search(r'\b(\w+)(?:\s+\1){3,}\b', raw_text.lower()):
                logger.error("🚨 Парсер: Обнаружен критический баг зацикливания LLM (Repetition Loop)!")
                # Принудительно вызываем ошибку, чтобы ReAct-цикл попробовал перегенерировать ответ
                raise ValueError("LLM generation loop detected")
            logger.info(
                "ℹ️ Парсер: Теги формата ReAct не найдены, но получен связный текст. Трактуем как Final Answer.")
            output.final_answer = text.strip()
            output.is_final = True

        #   Защита от "галлюцинированного цикла": если модель в ОДНОЙ реплике
        #   заявила и Action, и Final Answer — это физически невозможно в честном
        #   ReAct-цикле (между ними должен быть Observation от нашего кода,
        #   которого модель не могла видеть до реального вызова инструмента).
        #   Значит модель сама придумала результат инструмента — не доверяем
        #   такому Final Answer.
        if output.action and output.final_answer:
            logger.warning(
                f"⚠️ Обнаружен галлюцинированный цикл: модель заявила Action='{output.action}' "
                f"И Final Answer в одной реплике без реального Observation. "
                f"Final Answer отклонён, продолжаем цикл с реальным вызовом инструмента."
            )
            output.final_answer = ""
            output.is_final = False

            # Обрезаем raw_output до конца Action Input первого действия —
            # дальше в тексте модель сама выдумала Observation/Plan Update/второй
            # Action/Final Answer. Если положить это в историю сообщений целиком,
            # на следующей итерации LLM увидит свою же фантазию как будто это
            # реальный результат БД — и продолжит галлюцинировать дальше.
            cutoff_match = re.search(
                r'Action\s*Input\s*[:：-].*?(?=\n|\Z)',
                text, re.DOTALL | re.IGNORECASE
            )
            if cutoff_match:
                output.raw_output = text[:cutoff_match.end()].strip()
                logger.warning(
                    f"✂️ raw_output обрезан до конца Action Input, "
                    f"отброшено {len(text) - cutoff_match.end()} символов выдуманного продолжения."
                )
        if not output.thought and not output.final_answer:
            logger.warning("Модель сошла с формата: не найдено ни Thought, ни Final Answer.")

        return output


# Глобальный синглтон для импорта в сервисах
agent_parser = RobustReActParser()