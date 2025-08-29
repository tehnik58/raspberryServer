#!/usr/bin/env python3
"""
Скрипт-обертка для выполнения пользовательского кода
с правильной настройкой окружения эмуляции
"""
import json
import sys
import os

if os.getenv("SYSTEM_MODEL_JSON"):
    system_components = json.loads(os.getenv("SYSTEM_MODEL_JSON"))
else:
    system_components = {}

globals()["SYSTEM_MODEL"] = system_components

# Добавляем текущую директорию в путь поиска модулей
sys.path.insert(0, '/app')

# Подменяем стандартные модули на наши эмуляции
sys.modules['RPi'] = type(sys)('RPi')
sys.modules['RPi.GPIO'] = __import__('custom_gpio')
sys.modules['spidev'] = __import__('custom_spi')
sys.modules['smbus'] = __import__('custom_i2c')
sys.modules['smbus2'] = __import__('custom_i2c')
sys.modules['spidev'] = __import__('custom_spi')

# Импортируем эмулированные модули
from custom_gpio import GPIO, PWM
from custom_spi import spi
from custom_i2c import i2c, SMBus
from custom_components import components

# Делаем модули доступными в глобальной области видимости
globals()['GPIO'] = GPIO
globals()['PWM'] = PWM
globals()['spi'] = spi
globals()['i2c'] = i2c
globals()['SMBus'] = SMBus
globals()['temperature'] = components.read_temperature
globals()['humidity'] = components.read_humidity
globals()['distance'] = components.read_distance
globals()['set_led'] = components.set_led
globals()['read_button'] = components.read_button
globals()['create_motor'] = components.create_motor
globals()['create_stepper'] = components.create_stepper
globals()['get_motor_status'] = components.get_motor_status
globals()['get_stepper_position'] = components.get_stepper_position

def execute_code(code):
    """Выполняет Python код в правильном окружении"""
    try:
        # Создаем локальное пространство имен с нашими модулями
        local_vars = globals().copy()
        local_vars.update({
            '__name__': '__main__',
            '__file__': None,
            '__builtins__': __builtins__,
        })
        # Выполняем код
        exec(code, local_vars)
        return True
    except SyntaxError as e:
        print(f"SyntaxError: {e}")
        import traceback
        traceback.print_exc()
        return False
    except ImportError as e:
        print(f"ImportError: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"RuntimeError: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Читаем код из файла
        with open(sys.argv[1], 'r') as f:
            code = f.read()
    else:
        # Читаем код из stdin
        code = sys.stdin.read()
    
    success = execute_code(code)
    sys.exit(0 if success else 1)