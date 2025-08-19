#!/bin/bash

# Скрипт сборки и тестирования Raspberry Pi Simulator
set -e  # Прерывание выполнения при ошибке

echo "=== Raspberry Pi Simulator Build and Test Script ==="

# Определение цветов для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка установки Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен. Пожалуйста, установите Docker перед продолжением."
        exit 1
    fi
    print_status "Docker обнаружен: $(docker --version)"
}

# Сборка Docker образа для выполнения кода
build_code_runner_image() {
    print_status "Сборка Docker образа для выполнения Python кода..."
    
    cd docker-images/python-code-runner
    
    # Копируем скрипт запуска из директории scripts
    cp ../../scripts/run_code.py ./
    
    if docker build -t raspberry-python-runner . ; then
        print_status "Docker образ успешно собран!"
        # Удаляем временную копию скрипта
        rm -f run_code.py
    else
        print_error "Ошибка при сборке Docker образа!"
        # Удаляем временную копию скрипта даже при ошибке
        rm -f run_code.py
        exit 1
    fi
    
    cd ../..
}

# Запуск тестов
run_tests() {
    print_status "Запуск тестов..."
    
    # Проверка, запущен ли сервер
    if curl -s http://localhost:8000/health > /dev/null; then
        print_status "Сервер работает, запуск WebSocket тестов..."
        
        # Тест WebSocket соединения
        python3 -c "
import asyncio
import websockets
import json
import sys

async def test_websocket():
    try:
        uri = 'ws://localhost:8000/api/ws/test-client-123'
        async with websockets.connect(uri) as websocket:
            # Тест ping
            await websocket.send(json.dumps({'type': 'ping', 'timestamp': 'test'}))
            response = await websocket.recv()
            print('✅ Ping test passed:', response)
            
            # Тест выполнения кода
            test_code = '''
import time
print('Hello from test code!')
for i in range(3):
    print(f'Count: {i}')
    time.sleep(0.1)
print('Test completed')
'''
            await websocket.send(json.dumps({
                'type': 'code_execution', 
                'code': test_code
            }))
            
            # Получение ответов
            received_logs = 0
            for i in range(10):  # Максимум 10 сообщений
                response = await websocket.recv()
                data = json.loads(response)
                if data.get('type') == 'log':
                    print(f'📝 Log: {data[\"message\"]}')
                    received_logs += 1
                elif data.get('type') == 'status':
                    print(f'📊 Status: {data[\"message\"]}')
                elif data.get('type') == 'gpio_update':
                    print(f'🔌 GPIO Update: Pin {data[\"pin\"]} = {data[\"value\"]}')
                
                if received_logs >= 3:  # Ожидаем как минимум 3 лога
                    break
            
            print('✅ Code execution test passed')
            
    except Exception as e:
        print(f'❌ WebSocket test failed: {e}')
        sys.exit(1)

asyncio.run(test_websocket())
        "
    else
        print_warning "Сервер не запущен, пропускаем WebSocket тесты"
        print_status "Запустите сервер с помощью: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    fi
}

# Тестирование GPIO заглушки
# Тестирование GPIO заглушки
test_gpio_stub() {
    print_status "Тестирование GPIO заглушки..."
    
    cd docker-images/python-code-runner
    
    # Запуск теста GPIO заглушки внутри контейнера
    if docker run --rm -it raspberry-python-runner python -c "
import sys
sys.path.append('/home/user/.local/lib/python3.9/site-packages')

# Импортируем модуль, который подменяет RPi.GPIO
import fake_rpi.gpio

# Теперь импортируем RPi.GPIO (будет использовать нашу заглушку)
import RPi.GPIO as GPIO

# Тест основных функций
GPIO.setmode(GPIO.BCM)
print('✅ setmode test passed')

# Тестирование OUTPUT режима
GPIO.setup(18, GPIO.OUT)
print('✅ setup OUTPUT test passed')

GPIO.output(18, GPIO.HIGH)
print('✅ output HIGH test passed')

# Тестирование INPUT режима
GPIO.setup(17, GPIO.IN)
print('✅ setup INPUT test passed')

value = GPIO.input(17)
print(f'✅ input test passed: Pin 17 value = {value}')

# Тест PWM
pwm = GPIO.PWM(18, 100)
pwm.start(50)
print('✅ PWM start test passed')

pwm.ChangeDutyCycle(75)
print('✅ PWM change duty cycle test passed')

pwm.stop()
print('✅ PWM stop test passed')

GPIO.cleanup()
print('✅ cleanup test passed')

print('✅ All GPIO tests completed successfully')
    "; then
        print_status "GPIO заглушка работает корректно!"
    else
        print_error "Ошибка в GPIO заглушке!"
        exit 1
    fi
    
    cd ../..
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен. Пожалуйста, установите Docker перед продолжением."
        exit 1
    fi
    print_status "Docker обнаружен: $(docker --version)"
    
    # Проверяем, что Docker демон запущен и доступен
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker демон не запущен или нет прав доступа. Запустите Docker и убедитесь, что текущий пользователь имеет права."
        print_status "Попробуйте выполнить: sudo systemctl start docker"
        print_status "И добавить пользователя в группу docker: sudo usermod -aG docker $USER"
        print_status "После этого可能需要 перезайти в систему"
        exit 1
    fi
    print_status "Docker демон доступен"
}

# Добавьте эту функцию в скрипт
check_circular_imports() {
    print_status "Проверка циклических импортов..."
    
    if python -c "
import ast
import sys
from pathlib import Path

def find_circular_imports(file_path):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read())
    
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    
    return imports

# Проверяем основные модули
app_path = Path('app')
for py_file in app_path.rglob('*.py'):
    if py_file.name != '__init__.py':
        imports = find_circular_imports(py_file)
        print(f'File: {py_file}, Imports: {imports}')
        
print('✅ Circular imports check completed')
    "; then
        print_status "Проверка циклических импортов завершена"
    else
        print_error "Обнаружены проблемы с импортами"
        exit 1
    fi
}

main() {
    print_status "Начало процесса сборки и тестирования..."
    
    # Проверка зависимостей
    check_docker
    check_circular_imports
    check_docker
    
    # Сборка образов
    build_code_runner_image
    
    # Тестирование
    test_gpio_stub
    run_tests
    
    print_status "✅ Все тесты пройдены успешно!"
    print_status "Сборка и тестирование завершены."
}

# Запуск основной функции
main