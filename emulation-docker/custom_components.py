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
        self.motors = {}
        self.steppers = {}

    def create_motor(self, name):
        """Создает новый мотор"""
        self.motors[name] = self.MotorDriver(name)
        return self.motors[name]

    def create_stepper(self, name, steps_per_revolution=200):
        """Создает новый шаговый мотор"""
        self.steppers[name] = self.StepperMotor(name, steps_per_revolution)
        return self.steppers[name]

    def get_motor_status(self, name):
        """Возвращает статус мотора"""
        if name in self.motors:
            return self.motors[name].get_status()
        return None

    def get_stepper_position(self, name):
        """Возвращает позицию шагового мотора"""
        if name in self.steppers:
            return self.steppers[name].get_position()
        return None
    
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
    
    class MotorDriver:
        def __init__(self, name):
            self.name = name
            self.speed = 0
            self.direction = 1  # 1 вперед, -1 назад
            self.is_running = False

        def set_speed(self, speed):
            self.speed = max(-100, min(100, speed))
            print(f"Motor {self.name} speed set to {self.speed}%")

        def set_direction(self, direction):
            self.direction = 1 if direction else -1
            dir_text = "forward" if self.direction == 1 else "backward"
            print(f"Motor {self.name} direction set to {dir_text}")

        def stop(self):
            self.speed = 0
            self.is_running = False
            print(f"Motor {self.name} stopped")

        def get_status(self):
            return {
                'speed': self.speed,
                'direction': self.direction,
                'running': self.is_running
            }

    class StepperMotor:
        def __init__(self, name, steps_per_revolution=200):
            self.name = name
            self.steps_per_revolution = steps_per_revolution
            self.current_step = 0
            self.target_step = 0
            self.speed = 0  # steps per second
            self.is_running = False

        def move(self, steps):
            self.target_step = self.current_step + steps
            self.is_running = True
            print(f"Stepper {self.name} moving {steps} steps")

        def set_speed(self, speed):
            self.speed = speed
            print(f"Stepper {self.name} speed set to {speed} steps/sec")

        def get_position(self):
            return self.current_step

        def stop(self):
            self.is_running = False
            print(f"Stepper {self.name} stopped")

# Глобальный экземпляр для использования
components = EmulatedComponents()