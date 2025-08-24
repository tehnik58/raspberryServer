"""
Основной скрипт для выполнения пользовательского кода
"""
import sys
import os

# Добавляем текущую директорию в путь поиска модулей
sys.path.insert(0, '/app')

# Подменяем стандартные модули на наши эмуляции
try:
    # Пытаемся импортировать нашу эмуляцию
    from RPi import GPIO
    sys.modules['RPi'] = type(sys)('RPi')
    sys.modules['RPi.GPIO'] = GPIO
except ImportError as e:
    print(f"Error importing RPi.GPIO: {e}")
    # Если не получается, используем fallback
    import custom_gpio
    sys.modules['RPi'] = type(sys)('RPi')
    sys.modules['RPi.GPIO'] = custom_gpio

# Добавляем наши эмулированные компоненты в глобальную область видимости
from custom_components import components
temperature = components.read_temperature
humidity = components.read_humidity
distance = components.read_distance
set_led = components.set_led
read_button = components.read_button

# Выполняем пользовательский код
if __name__ == "__main__":
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        # Выполнение из файла
        with open(sys.argv[1], 'r') as f:
            code = f.read()
        exec(code)
    else:
        # Интерактивный режим
        print("Raspberry Pi Emulator - Interactive Mode")
        print("Available components: GPIO, temperature(), humidity(), distance()")
        print("Type 'exit()' to quit")
        
        while True:
            try:
                user_input = input(">>> ")
                if user_input.strip() == 'exit()':
                    break
                exec(user_input)
            except Exception as e:
                print(f"Error: {e}")