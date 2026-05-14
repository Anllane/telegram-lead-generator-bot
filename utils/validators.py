"""
Модуль валидации и форматирования данных
"""

import re
from typing import Optional, Tuple


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Валидация номера телефона
    
    Args:
        phone: Строка с номером телефона
        
    Returns:
        Tuple[bool, str]: (валидный ли номер, сообщение об ошибке или отформатированный номер)
    """
    if not phone or not phone.strip():
        return False, "Номер телефона не может быть пустым"
    
    # Удаление всех символов кроме цифр, +, -, пробелов
    cleaned_phone = re.sub(r'[^\d\-\+\s]', '', phone.strip())
    
    # Проверка, что номер содержит только разрешенные символы
    if not re.fullmatch(r'^[\d\-\+\s]+$', cleaned_phone):
        return False, "Номер содержит недопустимые символы"
    
    # Удаление всех пробелов и дефисов для проверки длины
    digits_only = re.sub(r'[\-\+\s]', '', cleaned_phone)
    
    if len(digits_only) < 10 or len(digits_only) > 15:
        return False, "Номер должен содержать от 10 до 15 цифр"
    
    # Проверка, что номер начинается с + или цифры
    if not re.match(r'^[\+]?[\d]', cleaned_phone):
        return False, "Номер должен начинаться с + или цифры"
    
    # Форматирование номера для красивого отображения
    formatted_phone = format_phone(cleaned_phone)
    
    return True, formatted_phone


def format_phone(phone: str) -> str:
    """
    Форматирование номера телефона для красивого отображения
    
    Args:
        phone: Строка с номером телефона
        
    Returns:
        Отформатированный номер телефона
    """
    if not phone:
        return ""
    
    # Удаление всех пробелов и дефисов для проверки длины
    digits_only = re.sub(r'[\-\+\s]', '', phone)
    
    # Если номер начинается с +7 и имеет 11 цифр
    if digits_only.startswith('7') and len(digits_only) == 11:
        return f"+7 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:10]}"
    
    # Если номер начинается с +8 и имеет 11 цифр
    elif digits_only.startswith('8') and len(digits_only) == 11:
        return f"+8 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:10]}"
    
    # Если номер начинается с + и имеет от 10 до 15 цифр
    elif digits_only.startswith('+') and 10 <= len(digits_only) <= 15:
        return phone
    
    # Для остальных случаев просто убираем лишние пробелы
    return re.sub(r'\s+', ' ', phone.strip())


def validate_name(name: str) -> Tuple[bool, str]:
    """
    Валидация имени пользователя
    
    Args:
        name: Строка с именем
        
    Returns:
        Tuple[bool, str]: (валидное ли имя, сообщение об ошибке или очищенное имя)
    """
    if not name or not name.strip():
        return False, "Имя не может быть пустым"
    
    cleaned_name = name.strip()
    
    if len(cleaned_name) < 2:
        return False, "Имя должно содержать минимум 2 символа"
    
    if len(cleaned_name) > 50:
        return False, "Имя слишком длинное"
    
    # Проверка, что имя содержит только буквы, пробелы и дефисы
    if not re.fullmatch(r'^[а-яА-ЯёЁa-zA-Z\s\-]+$', cleaned_name):
        return False, "Имя содержит недопустимые символы"
    
    return True, cleaned_name.strip()


def escape_markdown(text: str) -> str:
    """
    Экранирование символов для Markdown
    
    Args:
        text: Текст для экранирования
        
    Returns:
        Безопасный текст для Markdown
    """
    # Символы, которые нужно экранировать в Markdown
    markdown_chars = r'_*[]()~`>#+-=|{}.!'
    
    escaped = ""
    for char in text:
        if char in markdown_chars:
            escaped += f'\\{char}'
        else:
            escaped += char
    
    return escaped


def escape_html(text: str) -> str:
    """
    Экранирование символов для HTML
    
    Args:
        text: Текст для экранирования
        
    Returns:
        Безопасный текст для HTML
    """
    html_escape = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }
    
    return ''.join(html_escape.get(char, char) for char in text)