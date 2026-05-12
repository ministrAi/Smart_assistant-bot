import psycopg2
from config import TEST_DB_URL
from services.database import add_fact, get_facts, deactivate_fact


def test_facts(test_db):
    """Тестируем добавление/получение/удаление факта"""
    # Arrange
    user_id = 123
    fact =  "Люблю Python"
    importance = "low"
    # Act
    add_fact(user_id, fact, importance)
    facts = get_facts(user_id)
    # Assert
    assert len(facts) == 1
    assert facts[0]["id"] == 1
    assert facts[0]["content"] == "Люблю Python"
    assert facts[0]["importance"] == "low"
    fact_id = facts[0]["id"]
    # Act
    deactivate_fact(fact_id, user_id)
    facts = get_facts(user_id)
    # Assert
    assert len(facts) == 0



def test_facts_isolation(test_db):
    """Тест изоляции фактов между разными пользователями"""
    user_id1 = 123
    user_id2 = 456
    fact1 = "Люблю Python"
    fact2 = "Люблю C"
    importance1 = "low"
    importance2 = "medium"

    add_fact(user_id1, fact1, importance1)
    add_fact(user_id2, fact2, importance2)
    get_facts1 = get_facts(user_id1)
    get_facts2 = get_facts(user_id2)

    assert len(get_facts1) == 1
    assert get_facts1[0]["content"] == "Люблю Python"
    assert len(get_facts2) ==1
    assert get_facts2[0]["content"] == "Люблю C"



def test_deactivate_is_soft_delete(test_db):
    # Тестируем проверку, что записать остается в таблице после деактивации
    user_id = 123

    add_fact(user_id, "Люблю Python", "low")
    facts = get_facts(user_id)
    fact_id = facts[0]["id"]
    deactivate_fact(fact_id, user_id)
    conn = psycopg2.connect(TEST_DB_URL)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT is_active FROM LongTermMemory WHERE id = %s
    """, (fact_id,))
    row = cursor.fetchone()

    assert row[0] == 0
    conn.close()