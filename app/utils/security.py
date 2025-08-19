import re
from typing import Optional

def validate_client_id(client_id: str) -> bool:
    """
    Проверка валидности client_id
    """
    if not client_id or len(client_id) > 50:
        return False
    
    # Разрешаем только буквы, цифры и дефисы
    pattern = r'^[a-zA-Z0-9-]+$'
    return bool(re.match(pattern, client_id))

def sanitize_input(input_str: str, max_length: int = 1000) -> Optional[str]:
    """
    Очистка входных данных от потенциально опасных символов
    """
    if not input_str or len(input_str) > max_length:
        return None
    
    # Удаляем потенциально опасные символы
    cleaned = re.sub(r'[<>{}[\]\\]', '', input_str)
    return cleaned