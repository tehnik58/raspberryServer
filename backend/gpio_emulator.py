from typing import Dict, List
import json
import os

class GPIOEmulator:
    def __init__(self):
        self.output_pin_states: Dict[int, bool] = {}
        self.input_pin_states: Dict[int, bool] = {}
        self.pwm_states: Dict[int, Dict[str, any]] = {}
        self.spi_devices: List[Dict] = []  # Для отслеживания SPI устройств
        self.i2c_devices: List[Dict] = []  # Для отслеживания I2C устройств
        self.states_file = "/app/gpio_states/states.json"
        self._ensure_states_file_exists()
    
    def update_pwm_state(self, pin: int, duty_cycle: float, frequency: float = 100):
        """Обновляет состояние PWM пина"""
        self.pwm_states[pin] = {
            'duty_cycle': duty_cycle,
            'frequency': frequency,
            'active': duty_cycle > 0
        }
    
    def get_pwm_state(self, pin: int) -> Dict[str, any]:
        """Возвращает состояние PWM пина"""
        return self.pwm_states.get(pin, {
            'duty_cycle': 0,
            'frequency': 100,
            'active': False
        })
    
    def reset_all_pins(self):
        """Сбрасывает все пины в неактивное состояние"""
        self.output_pin_states.clear()
        self.pwm_states.clear()
        
    def _ensure_states_file_exists(self):
        os.makedirs(os.path.dirname(self.states_file), exist_ok=True)
        if not os.path.exists(self.states_file):
            with open(self.states_file, 'w') as f:
                json.dump({}, f)

    def _read_states(self):
        try:
            with open(self.states_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def _write_states(self):
        with open(self.states_file, 'w') as f:
            json.dump(self.input_pin_states, f)

    def update_output_pin_state(self, pin: int, state: bool):
        """Обновляет состояние выходного GPIO пина"""
        self.output_pin_states[pin] = state

    def get_output_pin_state(self, pin: int) -> bool:
        """Возвращает состояние выходного GPIO пина"""
        return self.output_pin_states.get(pin, False)

    def update_input_pin_state(self, pin: int, state: bool):
        """Обновляет состояние входного GPIO пина и сохраняет в файл"""
        self.input_pin_states[str(pin)] = state
        self._write_states()

    def get_input_pin_state(self, pin: int) -> bool:
        """Возвращает состояние входного GPIO пина"""
        return self.input_pin_states.get(str(pin), False)

    def reset_all_pins(self):
        """Сбрасывает все пины в неактивное состояние"""
        self.output_pin_states.clear()

    def add_spi_device(self, bus: int, device: int, device_type: str):
        """Добавляет SPI устройство для отслеживания"""
        self.spi_devices.append({
            'bus': bus,
            'device': device,
            'type': device_type,
            'active': False
        })
    
    def add_i2c_device(self, address: int, device_type: str):
        """Добавляет I2C устройство для отслеживания"""
        self.i2c_devices.append({
            'address': address,
            'type': device_type,
            'active': False
        })
    
    def update_spi_activity(self, bus: int, device: int, active: bool):
        """Обновляет состояние активности SPI устройства"""
        for dev in self.spi_devices:
            if dev['bus'] == bus and dev['device'] == device:
                dev['active'] = active
                break
    
    def update_i2c_activity(self, address: int, active: bool):
        """Обновляет состояние активности I2C устройства"""
        for dev in self.i2c_devices:
            if dev['address'] == address:
                dev['active'] = active
                break