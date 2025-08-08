class EmulatedGPIO:
    def __init__(self):
        self.pins = {i: {"mode": None, "value": 0} for i in range(40)}
    
    def setup(self, pin, mode):
        self.pins[pin]["mode"] = mode
    
    def output(self, pin, value):
        self.pins[pin]["value"] = value

class GPIOEmulator:
    # Константы режимов
    OUT = 1
    IN = 0
    HIGH = 1
    LOW = 0
    BCM = 11
    BOARD = 10

    def __init__(self, pin_config=None):
        self._mode = GPIOEmulator.BCM  # По умолчанию BCM нумерация
        self.pins = {}
        if pin_config:
            for pin, mode in pin_config.items():
                self.setup(int(pin), mode)

    def setmode(self, mode):
        """Установка нумерации пинов (BCM/BOARD)"""
        self._mode = mode

    def setup(self, pin, mode):
        """Настройка пина"""
        self.pins[pin] = {
            'mode': mode,
            'value': 0,
            'pull_up_down': None
        }

    def output(self, pin, value):
        """Установка значения выхода"""
        if pin not in self.pins:
            raise RuntimeError(f"Pin {pin} not configured")
        self.pins[pin]['value'] = value

    def input(self, pin):
        """Чтение значения входа"""
        return self.pins.get(pin, {}).get('value', 0)

    def cleanup(self):
        """Сброс всех настроек"""
        self.pins.clear()

    def get_state(self):
        """Текущее состояние всех пинов"""
        return {str(pin): data for pin, data in self.pins.items()}