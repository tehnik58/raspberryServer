"""
Эмуляция SPI интерфейса для Raspberry Pi
"""
import time
import random
import struct
import json
import os

class SpiDev:
    def __init__(self):
        self._bus = 0
        self._device = 0
        self._max_speed_hz = 500000
        self._mode = 0
        self._bits_per_word = 8
        self._cshigh = False
        self._lsbfirst = False
        self._connected = False
        
        # Эмулированные устройства на шине
        self._devices = {
            # ADC MCP3008
            0: {
                'type': 'mcp3008',
                'channels': [0] * 8,
                'vref': 3.3
            },
            # LED strip WS2812
            1: {
                'type': 'ws2812',
                'leds': [(0, 0, 0)] * 60  # RGB values
            }
        }
        
        # Файл для сохранения состояний
        self._states_file = "/app/spi_states.json"
        self._load_states()
        
        print("SPI emulator initialized")
        
    def xfer(self, data, speed_hz=0, delay_usecs=0, bits_per_word=0, cs_change=False):
        if not self._connected:
            raise RuntimeError("SPI device not open")
        
        speed = speed_hz if speed_hz > 0 else self._max_speed_hz
        bits = bits_per_word if bits_per_word > 0 else self._bits_per_word
        
        print(f"SPI transfer: {data} (speed: {speed}Hz, delay: {delay_usecs}μs)")
        # Отправляем событие передачи SPI
        self._send_spi_event("transfer", self._bus, self._device, data)
        
        # Обработка для разных типов устройств
        response = self._handle_device_request(data)
        
        return response
    
    def _send_spi_event(self, event_type, bus, device, data):
        """Отправляет событие SPI через stdout"""
        event = {
            "type": "spi_event",
            "event": event_type,
            "bus": bus,
            "device": device,
            "data": data
        }
        print(f"@@EMU_EVENT:{json.dumps(event)}")

    def _load_states(self):
        """Загружает сохраненные состояния из файла"""
        try:
            if os.path.exists(self._states_file):
                with open(self._states_file, 'r') as f:
                    states = json.load(f)
                    # Восстанавливаем состояния каналов ADC
                    if 'mcp3008' in states and 'channels' in states['mcp3008']:
                        self._devices[0]['channels'] = states['mcp3008']['channels']
        except:
            print("Failed to load SPI states")
    
    def _save_states(self):
        """Сохраняет текущие состояния в файл"""
        try:
            states = {
                'mcp3008': {
                    'channels': self._devices[0]['channels']
                }
            }
            with open(self._states_file, 'w') as f:
                json.dump(states, f)
        except:
            print("Failed to save SPI states")
    
    def open(self, bus, device):
        self._bus = bus
        self._device = device
        self._connected = True
        print(f"SPI opened: bus={bus}, device={device}")
        return True
    
    def close(self):
        self._connected = False
        print("SPI closed")
    
    def xfer(self, data, speed_hz=0, delay_usecs=0, bits_per_word=0, cs_change=False):
        if not self._connected:
            raise RuntimeError("SPI device not open")
        
        speed = speed_hz if speed_hz > 0 else self._max_speed_hz
        bits = bits_per_word if bits_per_word > 0 else self._bits_per_word
        
        print(f"SPI transfer: {data} (speed: {speed}Hz, delay: {delay_usecs}μs)")
        
        # Эмуляция задержки передачи
        if delay_usecs > 0:
            time.sleep(delay_usecs / 1000000)
        
        # Обработка для разных типов устройств
        response = self._handle_device_request(data)
        
        return response
    
    def xfer2(self, data, speed_hz=0, delay_usecs=0, bits_per_word=0, cs_change=False):
        # То же что и xfer, но с сохранением CS
        return self.xfer(data, speed_hz, delay_usecs, bits_per_word, cs_change)
    
    def readbytes(self, length):
        if not self._connected:
            raise RuntimeError("SPI device not open")
        
        # Генерируем случайные данные для чтения
        response = [random.randint(0, 255) for _ in range(length)]
        print(f"SPI read {length} bytes: {response}")
        return response
    
    def writebytes(self, data):
        if not self._connected:
            raise RuntimeError("SPI device not open")
        
        print(f"SPI write: {data}")
        return self._handle_device_request(data)
    
    def _handle_device_request(self, data):
        """Обрабатывает запросы к эмулированным устройствам"""
        if self._device not in self._devices:
            # Возвращаем случайные данные для неизвестных устройств
            return [random.randint(0, 255) for _ in range(len(data))]
        
        device_type = self._devices[self._device]['type']
        
        if device_type == 'mcp3008':
            return self._handle_mcp3008(data)
        elif device_type == 'ws2812':
            return self._handle_ws2812(data)
        
        return [0] * len(data)
    
    def _handle_mcp3008(self, data):
        """Обрабатывает запросы к ADC MCP3008"""
        if len(data) < 3:
            return [0] * 3
        
        # Получаем информацию об устройстве
        device_info = self._devices[self._device]
        
        # Формат запроса MCP3008
        # byte 0: start bit (1)
        # byte 1: configuration: single-ended(1)/differential(0), channel (3 bits)
        # byte 2: don't care
        
        start_bit = (data[0] >> 7) & 0x01
        sgl_diff = (data[1] >> 7) & 0x01
        channel = (data[1] >> 4) & 0x07
        
        if start_bit != 1:
            return [0, 0, 0]
        
        # Читаем значение из эмулированного канала
        value = device_info['channels'][channel]
        # Конвертируем в 10-битное значение (0-1023)
        adc_value = int(min(max(value, 0), 3.3) / 3.3 * 1023)
        
        # Формат ответа MCP3008
        # byte 0: don't care
        # byte 1: high 2 bits of result
        # byte 2: low 8 bits of result
        return [0, (adc_value >> 8) & 0x03, adc_value & 0xFF]
    
    def _handle_ws2812(self, data):
        """Обрабатывает запросы к WS2812 LED strip"""
        # WS2812 использует специальный протокол, не стандартный SPI
        # Здесь просто логируем данные
        print(f"WS2812 data: {data}")
        return []
    
    def set_adc_channel_value(self, channel, value):
        """Устанавливает значение для канала ADC"""
        if self._device == 0 and channel < 8:
            self._devices[0]['channels'][channel] = value
            self._save_states()
            print(f"ADC channel {channel} set to {value}V")
    
    def get_adc_channel_value(self, channel):
        """Возвращает значение канала ADC"""
        if self._device == 0 and channel < 8:
            return self._devices[0]['channels'][channel]
        return 0
    
    # Свойства для совместимости с spidev
    @property
    def max_speed_hz(self):
        return self._max_speed_hz
    
    @max_speed_hz.setter
    def max_speed_hz(self, value):
        self._max_speed_hz = value
        print(f"SPI speed set to {value}Hz")
    
    @property
    def mode(self):
        return self._mode
    
    @mode.setter
    def mode(self, value):
        if value not in [0, 1, 2, 3]:
            raise ValueError("SPI mode must be 0, 1, 2, or 3")
        self._mode = value
        print(f"SPI mode set to {value}")
    
    @property
    def bits_per_word(self):
        return self._bits_per_word
    
    @bits_per_word.setter
    def bits_per_word(self, value):
        self._bits_per_word = value
        print(f"SPI bits per word set to {value}")
    
    @property
    def cshigh(self):
        return self._cshigh
    
    @cshigh.setter
    def cshigh(self, value):
        self._cshigh = value
        print(f"SPI CS high set to {value}")
    
    @property
    def lsbfirst(self):
        return self._lsbfirst
    
    @lsbfirst.setter
    def lsbfirst(self, value):
        self._lsbfirst = value
        print(f"SPI LSB first set to {value}")

# Глобальный экземпляр для импорта
spi = SpiDev()