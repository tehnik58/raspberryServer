import sys
import time

class GPIO:
    # Константы
    BCM = 11
    BOARD = 10
    OUT = 0
    IN = 1
    HIGH = 1
    LOW = 0
    PUD_UP = 22
    PUD_DOWN = 21
    PUD_OFF = 20

    # Режим нумерации пинов
    _mode = None
    
    # Состояние пинов
    _pins = {}
    
    # PWM эмуляция
    _pwm_instances = {}

    @classmethod
    def setmode(cls, mode):
        """Установка режима нумерации пинов"""
        if mode not in [cls.BCM, cls.BOARD]:
            raise ValueError("Invalid mode. Use GPIO.BCM or GPIO.BOARD")
        cls._mode = mode
        print(f"GPIO_ACTION: SETMODE {mode}")

    @classmethod
    def setup(cls, pin, mode, pull_up_down=None):
        """Настройка пина"""
        cls._validate_pin(pin)
        
        cls._pins[pin] = {
            "mode": mode,
            "value": cls.LOW,
            "pull_up_down": pull_up_down
        }
        
        print(f"GPIO_ACTION: SETUP pin={pin}, mode={mode}")

    @classmethod
    def output(cls, pin, value):
        """Установка значения пина в режиме OUTPUT"""
        cls._validate_pin(pin)
        cls._validate_pin_mode(pin, cls.OUT)
        
        cls._pins[pin]["value"] = value
        print(f"GPIO_ACTION: OUTPUT pin={pin}, value={value}")

    @classmethod
    def input(cls, pin):
        """Чтение значения пина в режиме INPUT"""
        cls._validate_pin(pin)
        cls._validate_pin_mode(pin, cls.IN)
        
        value = cls._pins[pin]["value"]
        print(f"GPIO_ACTION: INPUT pin={pin}, value={value}")
        return value

    @classmethod
    def PWM(cls, pin, frequency):
        """Создание PWM instance (эмуляция)"""
        cls._validate_pin(pin)
        
        class PWMEmulator:
            def __init__(self, pin, frequency):
                self.pin = pin
                self.frequency = frequency
                self.duty_cycle = 0
                self.running = False
                
            def start(self, duty_cycle):
                self.duty_cycle = duty_cycle
                self.running = True
                print(f"GPIO_ACTION: PWM_START pin={self.pin}, duty_cycle={duty_cycle}")
                
            def ChangeDutyCycle(self, duty_cycle):
                self.duty_cycle = duty_cycle
                print(f"GPIO_ACTION: PWM_CHANGE pin={self.pin}, duty_cycle={duty_cycle}")
                
            def ChangeFrequency(self, frequency):
                self.frequency = frequency
                print(f"GPIO_ACTION: PWM_CHANGE_FREQ pin={self.pin}, frequency={frequency}")
                
            def stop(self):
                self.running = False
                print(f"GPIO_ACTION: PWM_STOP pin={self.pin}")
        
        pwm_instance = PWMEmulator(pin, frequency)
        cls._pwm_instances[pin] = pwm_instance
        return pwm_instance

    @classmethod
    def cleanup(cls, pin=None):
        """Очистка настроек GPIO"""
        if pin is None:
            cls._pins.clear()
            cls._pwm_instances.clear()
            print("GPIO_ACTION: CLEANUP_ALL")
        else:
            cls._validate_pin(pin)
            if pin in cls._pins:
                del cls._pins[pin]
            if pin in cls._pwm_instances:
                del cls._pwm_instances[pin]
            print(f"GPIO_ACTION: CLEANUP pin={pin}")

    @classmethod
    def setwarnings(cls, flag):
        """Игнорируем предупреждения в эмуляторе"""
        pass

    @classmethod
    def _validate_pin(cls, pin):
        """Проверка валидности номера пина"""
        if cls._mode is None:
            raise RuntimeError("Please set GPIO mode first using GPIO.setmode()")
            
        if not isinstance(pin, int) or pin < 0:
            raise ValueError("Invalid pin number")

    @classmethod
    def _validate_pin_mode(cls, pin, expected_mode):
        """Проверка режима пина"""
        if pin not in cls._pins:
            raise RuntimeError(f"Pin {pin} is not setup. Use GPIO.setup() first")
            
        if cls._pins[pin]["mode"] != expected_mode:
            mode_str = "OUTPUT" if expected_mode == cls.OUT else "INPUT"
            raise RuntimeError(f"Pin {pin} is not in {mode_str} mode")

# Подмена настоящего модуля RPi.GPIO
sys.modules['RPi'] = type(sys)('RPi')
sys.modules['RPi.GPIO'] = GPIO()