from .base import init_db, get_connection
from .chat_history import (
    save_message,
    get_conversation_history,
    get_messages_for_task,
    delete_user_messages,
    hard_reset_communications
)
from .long_term import add_fact, get_facts, deactivate_fact
from .working_memory import set_task, get_task, clear_task
from .reflection_memory import save_reflection, get_reflection