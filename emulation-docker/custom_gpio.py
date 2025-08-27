"""
Кастомная реализация GPIO для эмуляции Raspberry Pi
"""
import json
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
PWM = 2

class PWM:
    def __init__(self, pin, frequency=100):
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = 0
        self.running = False
        print(f"PWM initialized on pin {pin} with frequency {frequency}Hz")
        # Отправляем событие инициализации PWM
        self._send_pwm_event("init", pin, frequency, 0)
        sys.stdout.flush()
    
    def start(self, duty_cycle):
        self.duty_cycle = duty_cycle
        self.running = True
        print(f"PWM started on pin {self.pin} with duty cycle {duty_cycle}%")
        # Отправляем событие старта PWM
        self._send_pwm_event("start", self.pin, self.frequency, duty_cycle)
        sys.stdout.flush()
    
    def ChangeDutyCycle(self, duty_cycle):
        self.duty_cycle = duty_cycle
        print(f"PWM duty cycle changed to {duty_cycle}% on pin {self.pin}")
        # Отправляем событие изменения скважности
        self._send_pwm_event("duty_change", self.pin, self.frequency, duty_cycle)
        sys.stdout.flush()
    
    def ChangeFrequency(self, frequency):
        self.frequency = frequency
        print(f"PWM frequency changed to {frequency}Hz on pin {self.pin}")
        # Отправляем событие изменения частоты
        self._send_pwm_event("freq_change", self.pin, frequency, self.duty_cycle)
        sys.stdout.flush()
    
    def stop(self):
        self.running = False
        print(f"PWM stopped on pin {self.pin}")
        # Отправляем событие остановки PWM
        self._send_pwm_event("stop", self.pin, self.frequency, 0)
        sys.stdout.flush()
    
    def _send_pwm_event(self, event_type, pin, frequency, duty_cycle):
        """Отправляет событие PWM через stdout"""
        event = {
            "type": "pwm_event",
            "event": event_type,
            "pin": pin,
            "frequency": frequency,
            "duty_cycle": duty_cycle
        }
        print(f"@@EMU_EVENT:{json.dumps(event)}")

class CustomGPIO:
    def __init__(self):
        self._mode = None
        self._pins = {}
        self._callbacks = {}
        self.states_file = "/app/gpio_states/states.json"
    
    def PWM(self, pin, frequency=100):
        """Создает PWM объект для указанного пина"""
        return self.PWM(pin, frequency)
    
    def input(self, pin):
        if pin not in self._pins or self._pins[pin]['mode'] != IN:
            raise RuntimeError(f"Pin {pin} is not set up as input")
        
        # Чтение состояния из файла
        try:
            with open(self.states_file, 'r') as f:
                states = json.load(f)
            value = states.get(str(pin), False)
        except:
            value = False
            
        print(f"GPIO {pin} input: {value}")
        sys.stdout.flush()
        time.sleep(0.1)
        return value
    
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