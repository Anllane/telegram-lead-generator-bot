"""
FSM-состояния для формы лидогенерации
"""

from aiogram.fsm.state import State, StatesGroup


class FormStates(StatesGroup):
    """Группа состояний для формы сбора лидов"""
    
    # Шаг 1: Запрос имени
    name = State()
    
    # Шаг 2: Запрос телефона с валидацией
    phone = State()
    
    # Шаг 3: Выбор услуги
    service = State()
    
    # Шаг 4: Финальная сводка перед отправкой
    summary = State()