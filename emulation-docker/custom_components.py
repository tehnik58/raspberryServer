"""
Эмуляция различных компонентов Raspberry Pi
"""
import time
import random

class EmulatedComponents:
    def __init__(self):
        self.sensors = {
            'temperature': 25.0,
            'humidity': 50.0,
            'distance': 20.0
        }
    
    def read_temperature(self):
        """Чтение температуры с эмулированного датчика"""
        self.sensors['temperature'] += random.uniform(-0.5, 0.5)
        return round(self.sensors['temperature'], 2)
    
    def read_humidity(self):
        """Чтение влажности с эмулированного датчика"""
        self.sensors['humidity'] += random.uniform(-1, 1)
        return round(max(0, min(100, self.sensors['humidity'])), 2)
    
    def read_distance(self):
        """Чтение расстояния с эмулированного датчика"""
        self.sensors['distance'] = random.uniform(5, 50)
        return round(self.sensors['distance'], 2)
    
    def set_led(self, pin, state):
        """Управление эмулированным светодиодом"""
        status = "ON" if state else "OFF"
        print(f"LED on pin {pin} is now {status}")
    
    def read_button(self, pin):
        """Чтение состояния эмулированной кнопки"""
        return random.choice([True, False])

# Глобальный экземпляр для использования
components = EmulatedComponents()