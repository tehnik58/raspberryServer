"""
Эмуляция I2C интерфейса для Raspberry Pi
"""
import json
import time
import random

class SMBus:
    def __init__(self, bus=None):
        self._bus = bus if bus is not None else 1
        self._address = None
        self._devices = {
            # BMP280 (temperature/pressure sensor)
            0x76: {
                'type': 'bmp280',
                'temperature': 25.0,
                'pressure': 1013.25,
                'registers': {
                    0xD0: 0x58,  # CHIP_ID
                    0x88: 0x00,  # CALIBRATION DATA...
                }
            },
            # LCD display
            0x27: {
                'type': 'lcd',
                'text': [''] * 4,
                'backlight': True
            }
        }
        
        print(f"I2C emulator initialized (bus {self._bus})")
    
    def open(self, bus):
        self._bus = bus
        print(f"I2C bus {bus} opened")
        return True
    
    def close(self):
        print("I2C closed")
        
    def _send_i2c_event(self, event_type, address, register, value):
        """Отправляет событие I2C через stdout"""
        event = {
            "type": "i2c_event",
            "event": event_type,
            "address": address,
            "register": register,
            "value": value
        }
        print(f"@@EMU_EVENT:{json.dumps(event)}")

    def write_byte_data(self, address, register, value):
        if address not in self._devices:
            print(f"I2C write to unknown device 0x{address:02X}, reg 0x{register:02X}: 0x{value:02X}")
            return
        
        device = self._devices[address]
        print(f"I2C write to 0x{address:02X}, reg 0x{register:02X}: 0x{value:02X}")
        # Отправляем событие записи I2C
        self._send_i2c_event("write", address, register, value)
        
        # Для BMP280 обновляем регистры
        if device['type'] == 'bmp280':
            device['registers'][register] = value
    
    def write_i2c_block_data(self, address, register, data):
        if address not in self._devices:
            print(f"I2C block write to unknown device 0x{address:02X}, reg 0x{register:02X}: {data}")
            return
        
        device = self._devices[address]
        print(f"I2C block write to 0x{address:02X}, reg 0x{register:02X}: {data}")
        
        # Для LCD обрабатываем блок данных
        if device['type'] == 'lcd':
            for byte in data:
                self._handle_lcd_write(address, byte)
    
    def read_byte(self, address):
        if address not in self._devices:
            print(f"I2C read from unknown device 0x{address:02X}")
            return random.randint(0, 255)
        
        device = self._devices[address]
        print(f"I2C read from 0x{address:02X}")
        
        # Для BMP280 возвращаем случайные данные
        if device['type'] == 'bmp280':
            # Обновляем значения датчика
            device['temperature'] += random.uniform(-0.1, 0.1)
            device['pressure'] += random.uniform(-0.1, 0.1)
            return random.randint(0, 255)
        
        return 0
    
    def read_byte_data(self, address, register):
        if address not in self._devices:
            print(f"I2C read from unknown device 0x{address:02X}, reg 0x{register:02X}")
            return random.randint(0, 255)
        
        device = self._devices[address]
        print(f"I2C read from 0x{address:02X}, reg 0x{register:02X}")
        
        # Для BMP280 возвращаем значение регистра
        if device['type'] == 'bmp280':
            if register in device['registers']:
                value = device['registers'][register]
                # Отправляем событие чтения I2C
                self._send_i2c_event("read", address, register, value)
                return value
            
            # Генерируем данные датчика для определенных регистров
            if register == 0xFA:  # TEMP_MSB
                temp = int(device['temperature'] * 100) & 0xFFFF
                value = (temp >> 8) & 0xFF
                self._send_i2c_event("read", address, register, value)
                return value
            
            return random.randint(0, 255)
        
        value = random.randint(0, 255)
        self._send_i2c_event("read", address, register, value)
        return value
    
    def read_i2c_block_data(self, address, register, length):
        if address not in self._devices:
            print(f"I2C block read from unknown device 0x{address:02X}, reg 0x{register:02X}, length {length}")
            return [random.randint(0, 255) for _ in range(length)]
        
        device = self._devices[address]
        print(f"I2C block read from 0x{address:02X}, reg 0x{register:02X}, length {length}")
        
        # Для BMP280 возвращаем блок данных
        if device['type'] == 'bmp280':
            result = []
            for i in range(length):
                reg_addr = register + i
                if reg_addr in device['registers']:
                    result.append(device['registers'][reg_addr])
                else:
                    result.append(random.randint(0, 255))
            return result
        
        return [0] * length
    
    def _handle_lcd_write(self, address, value):
        """Обрабатывает запись в LCD дисплей"""
        device = self._devices[address]
        
        # Эмуляция команд LCD
        if value == 0x01:  # Clear display
            device['text'] = [''] * 4
            print("LCD: Clear display")
        elif value == 0x02:  # Return home
            print("LCD: Return home")
        elif value & 0x80:  # Set DDRAM address
            addr = value & 0x7F
            print(f"LCD: Set DDRAM address 0x{addr:02X}")
        # Другие команды...
        else:
            # Это символ для отображения
            char = chr(value)
            print(f"LCD: Display character '{char}'")
    
    # Методы для совместимости с smbus2
    def read_word_data(self, address, register):
        data = self.read_i2c_block_data(address, register, 2)
        return (data[0] << 8) | data[1]
    
    def write_word_data(self, address, register, value):
        self.write_i2c_block_data(address, register, [
            (value >> 8) & 0xFF, 
            value & 0xFF
        ])
    
    def read_block_data(self, address, register):
        return self.read_i2c_block_data(address, register, 32)  # SMBus block size
    
    def write_block_data(self, address, register, data):
        self.write_i2c_block_data(address, register, data)

# Глобальный экземпляр для импорта
i2c = SMBus()