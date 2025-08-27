🚀 Документация по серверной части проекта "Эмулятор Raspberry Pi для Web"
📋 Оглавление
Быстрый старт

Архитектура

API Endpoints

WebSocket API

Docker Manager

GPIO Emulator

Конфигурация

Безопасность

Мониторинг

Troubleshooting

🚀 Быстрый старт
Предварительные требования
Python 3.9+

Docker Engine

Docker Compose

Установка и запуск
bash

# Клонирование репозитория

git clone [https://github.com/tehnik58/raspberryServer.git](https://github.com/tehnik58/raspberryServer.git)

cd raspberry-emulator-web

# Запуск через Docker Compose (рекомендуется)

docker-compose up --build

# Или ручная установка

cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
Проверка работы
Откройте в браузере: <http://localhost:8000/docs> для доступа к Swagger UI

🏗️ Архитектура
text
FastAPI Server (port 8000)
├── WebSocket Endpoint (/ws/execute)
├── REST API Endpoints
├── Static Files Serving
├── Docker Manager
└── GPIO Emulator
Основные компоненты
main.py - Основное приложение FastAPI

websocket_manager.py - Управление WebSocket соединениями

docker_manager.py - Управление Docker контейнерами

gpio_emulator.py - Эмуляция GPIO пинов

custom_gpio.py - Кастомная реализация RPi.GPIO

📡 API Endpoints
GET / - Главная страница
Возвращает HTML интерфейс эмулятора

GET /api/status - Статус сервера
bash
curl <http://localhost:8000/api/status>
Response:

json
{
  "status": "running",
  "connected_clients": 3,
  "active_containers": 1,
  "gpio_states": {"18": true, "23": false}
}
POST /api/execute - Синхронное выполнение кода
bash
curl -X POST "<http://localhost:8000/api/execute>" \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello World\")"}'
Response:

json
{
  "output": "Hello World\n",
  "exit_code": 0,
  "execution_time": 0.15
}
GET /api/containers - Список контейнеров
bash
curl <http://localhost:8000/api/containers>
Response:

json
{
  "containers": [
    {
      "id": "abc123",
      "status": "running",
      "image": "rpi-emulator",
      "created": "2024-01-15T10:30:00Z"
    }
  ]
}
🔌 WebSocket API
Подключение
javascript
const ws = new WebSocket('ws://localhost:8000/ws/execute');
Формат сообщений
📤 От клиента к серверу:
Запуск выполнения кода:

json
{
  "type": "execute",
  "code": "import RPi.GPIO as GPIO\nGPIO.setup(18, GPIO.OUT)"
}
Остановка выполнения:

json
{
  "type": "stop"
}
📤 От клиента к серверу:
json
{
  "type": "gpio_input",
  "pin": 17,
  "state": true
}
📥 От сервера клиентам:
json
{
  "type": "gpio_state_update", 
  "pin": 18,
  "state": true,
  "mode": "output"
}
📊 Вывод выполнения кода:
json
{
  "type": "output",
  "content": "GPIO 18 output: True"
}

🐳 Docker Manager
Конфигурация контейнеров
python
DEFAULT_CONFIG = {
    'mem_limit': '100m',
    'network_mode': 'none',
    'stdout': True,
    'stderr': True,
    'auto_remove': True,
    'privileged': False,
    'user': 'emulator'
}
Методы API
python
class DockerManager:
    async def execute_code_realtime(code: str, output_callback: Callable) -> None
    async def execute_code(code: str) -> str
    async def get_container_stats(container_id: str) -> Dict
    async def stop_all_containers() -> None
📍 GPIO Emulator
Управление пинами
python
from gpio_emulator import GPIOEmulator

gpio = GPIOEmulator()

gpio.update_pin_state(18, True)    # Установить пин 18 в HIGH
state = gpio.get_pin_state(18)     # Получить состояние пина
gpio.reset_all_pins()              # Сбросить все пины
Эмулируемые компоненты
python
from custom_components import components

# Датчики

temp = components.read_temperature()    # Температура °C
humidity = components.read_humidity()   # Влажность %
distance = components.read_distance()   # Расстояние cm

# Управление

components.set_led(18, True)           # Включить LED на пине 18
button_state = components.read_button(23)  # Прочитать кнопку
⚙️ Конфигурация
Переменные окружения
Создайте файл .env в директории backend/:

env
DOCKER_HOST=unix:///var/run/docker.sock
MEMORY_LIMIT=100m
CPU_LIMIT=0.5
TIMEOUT=30
MAX_CONTAINERS=5
LOG_LEVEL=INFO
Docker Compose настройки
yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - DOCKER_HOST=unix:///var/run/docker.sock
🛡️ Безопасность
Ограничения выполнения кода
python
SAFE_MODULES = ['RPi.GPIO', 'time', 'random']
BLACKLISTED_KEYWORDS = [
    'import os', 'import subprocess', 'open(',
    '__import__', 'eval(', 'exec(', 'compile('
]
Валидация кода
python
def validate_code_safety(code: str) -> bool:
    for keyword in BLACKLISTED_KEYWORDS:
        if keyword in code:
            return False
    return True
Ограничения ресурсов
yaml
deploy:
  resources:
    limits:
      memory: 100M
      cpus: '0.5'
📊 Мониторинг
Структура логов
text
logs/
├── server.log          # Логи FastAPI
├── docker.log          # Логи Docker
├── websocket.log       # WebSocket соединения
└── execution.log       # Логи выполнения
Настройка логирования
python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/server.log'),
        logging.StreamHandler()
    ]
)
Метрики здоровья
bash

# Проверка здоровья

curl <http://localhost:8000/health>

# Метрики производительности

curl <http://localhost:8000/metrics>
🔄 Примеры использования
Пример 1: Мигание светодиодом
python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)

try:
    for i in range(10):
        GPIO.output(18, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(18, GPIO.LOW)
        time.sleep(0.5)
finally:
    GPIO.cleanup()
Пример 2: Работа с датчиками
python
import RPi.GPIO as GPIO
from custom_components import components

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN)

# Чтение датчиков

temp = components.read_temperature()
humidity = components.read_humidity()

print(f"Temperature: {temp}°C")
print(f"Humidity: {humidity}%")

# Чтение кнопки

if GPIO.input(23):
    print("Button pressed!")
🐳 Эмуляционный Docker образ
Структура образа
dockerfile
FROM python:3.9-slim
WORKDIR /app

RUN apt-get update && apt-get install -y gcc python3-dev
COPY custom_gpio.py /app/RPi/GPIO.py
COPY custom_components.py .
COPY runner.py .

ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV PYTHONUNBUFFERED=1

RUN useradd -m -u 1000 emulator
USER emulator

CMD ["python", "runner.py"]
Кастомная реализация GPIO
Эмулирует полный API RPi.GPIO:

GPIO.setmode()

GPIO.setup()

GPIO.output()

GPIO.input()

GPIO.cleanup()

🚀 Производительность
Production настройки
bash
uvicorn main:app --host 0.0.0.0 --port 8000 \
  --workers 4 \
  --limit-concurrency 100 \
  --timeout-keep-alive 30
Оптимизация
Асинхронная обработка запросов

Пулинг соединений к Docker

Кэширование часто используемых операций

Ограничение одновременных выполнений

🔧 Troubleshooting
Распространенные проблемы
Docker connection error

bash

# Проверка прав доступа

ls -la /var/run/docker.sock
sudo usermod -aG docker $USER
Image not found

bash
docker build -t rpi-emulator ./emulation-docker
Permission denied

bash
chmod 666 /var/run/docker.sock
WebSocket connection failed

bash

# Проверка firewall

sudo ufw allow 8000
Логи для отладки
python

# Включение детального логирования

import logging
logging.basicConfig(level=logging.DEBUG)
Диагностика
bash

# Проверка Docker

docker ps
docker images

# Проверка сетевых соединений

netstat -tulpn | grep 8000

# Просмотр логов

tail -f logs/server.log
📞 Поддержка
Для решения проблем:

Проверьте логи в logs/ директории

Убедитесь что Docker запущен: docker info

Проверьте доступность порта 8000

Убедитесь что образ rpi-emulator собран

Версия: 1.0.0
Последнее обновление: 2024-01-15
Лицензия: MIT License

Для дополнительной помощи обратитесь к документации FastAPI и Docker.
