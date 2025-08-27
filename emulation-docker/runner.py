"""
Сервис эмуляции Raspberry Pi
Просто импортирует все модули и ждет в фоновом режиме
"""
import time
import sys
import os

# Добавляем текущую директорию в путь поиска модулей
sys.path.insert(0, '/app')

# Импортируем все модули эмуляции
try:
    from custom_gpio import GPIO, PWM
    from custom_spi import spi
    from custom_i2c import i2c, SMBus
    from custom_components import components
    
    print("Raspberry Pi Emulator Service started successfully")
    print("All modules imported:")
    print("- GPIO module ready")
    print("- SPI module ready") 
    print("- I2C module ready")
    print("- Components module ready")
    
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def main():
    """Основная функция сервиса"""
    print("Service is running in background mode...")
    print("Press Ctrl+C to stop")
    
    try:
        # Бесконечный цикл для поддержания сервиса активным
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Service stopped by user")
    except Exception as e:
        print(f"Service error: {e}")

if __name__ == "__main__":
    main()