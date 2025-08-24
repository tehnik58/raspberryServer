import time
import random
from typing import Dict, Any

class EmulatedComponents:
    def __init__(self):
        self.gpio_state = {}
        self.sensor_data = {
            'temperature': 25.0,
            'humidity': 50.0,
            'distance': 20.0
        }
    
    def read_temperature(self) -> float:
        # Имитация изменения температуры
        self.sensor_data['temperature'] += random.uniform(-0.5, 0.5)
        return round(self.sensor_data['temperature'], 2)
    
    def read_humidity(self) -> float:
        # Имитация изменения влажности
        self.sensor_data['humidity'] += random.uniform(-1, 1)
        return round(max(0, min(100, self.sensor_data['humidity'])), 2)
    
    def read_distance(self) -> float:
        # Имитация измерения расстояния
        self.sensor_data['distance'] = random.uniform(5, 50)
        return round(self.sensor_data['distance'], 2)
    
    def set_gpio_state(self, pin: int, state: bool):
        self.gpio_state[pin] = state
        print(f"GPIO {pin} set to {state}")
    
    def get_gpio_state(self, pin: int) -> bool:
        return self.gpio_state.get(pin, False)

# Глобальный экземпляр для использования в скриптах
emulated_components = EmulatedComponents()