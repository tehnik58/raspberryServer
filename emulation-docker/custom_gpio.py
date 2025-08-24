"""
Кастомная реализация GPIO для эмуляции Raspberry Pi
"""
import time
import random
import sys

# Константы для совместимости с RPi.GPIO
BCM = 11
BOARD = 10
OUT = 0
IN = 1
HIGH = True
LOW = False
PUD_UP = 22
PUD_DOWN = 21
RISING = 31
FALLING = 32
BOTH = 33

class CustomGPIO:
    def __init__(self):
        self._mode = None
        self._pins = {}
        self._callbacks = {}
    
    def setmode(self, mode):
        """Устанавливает режим нумерации пинов"""
        self._mode = mode
        print(f"GPIO mode set to: {mode}")
        sys.stdout.flush()  # Принудительно сбрасываем буфер
    
    def setup(self, pin, mode, initial=None, pull_up_down=None):
        """Настраивает пин на вход или выход"""
        self._pins[pin] = {
            'mode': mode,
            'value': initial if initial is not None else False,
            'pull_up_down': pull_up_down
        }
        print(f"GPIO {pin} setup as {mode}")
        sys.stdout.flush()
    
    def output(self, pin, value):
        """Устанавливает состояние выходного пина"""
        if pin not in self._pins or self._pins[pin]['mode'] != OUT:
            raise RuntimeError(f"Pin {pin} is not set up as output")
        
        self._pins[pin]['value'] = value
        print(f"GPIO {pin} output: {value}")
        sys.stdout.flush()  # Принудительно сбрасываем буфер
        time.sleep(0.1)  # Небольшая задержка для эмуляции
    
    def input(self, pin):
        """Читает состояние входного пина"""
        if pin not in self._pins or self._pins[pin]['mode'] != IN:
            raise RuntimeError(f"Pin {pin} is not set up as input")
        
        # Эмуляция случайного значения для тестирования
        value = random.choice([True, False])
        print(f"GPIO {pin} input: {value}")
        sys.stdout.flush()
        time.sleep(0.1)
        return value
    
    def add_event_detect(self, pin, edge, callback=None, bouncetime=None):
        """Добавляет обнаружение событий на пине"""
        self._callbacks[pin] = callback
        print(f"Event detection added to pin {pin} for {edge} edge")
        sys.stdout.flush()
    
    def cleanup(self, pin=None):
        """Очищает настройки GPIO"""
        if pin:
            if pin in self._pins:
                del self._pins[pin]
            if pin in self._callbacks:
                del self._callbacks[pin]
            print(f"GPIO {pin} cleaned up")
        else:
            self._pins = {}
            self._callbacks = {}
            print("All GPIO cleaned up")
        sys.stdout.flush()

# Создаем глобальный экземпляр
GPIO = CustomGPIO()

# Делаем константы доступными на уровне модуля
setmode = GPIO.setmode
setup = GPIO.setup
output = GPIO.output
input = GPIO.input
cleanup = GPIO.cleanup
add_event_detect = GPIO.add_event_detect