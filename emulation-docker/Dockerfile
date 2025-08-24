FROM python:3.9-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем пакеты для эмуляции Raspberry Pi
RUN pip install requests

# Копируем кастомные файлы эмуляции
COPY custom_gpio.py .
COPY custom_components.py .
COPY runner.py .

# Создаем правильную структуру пакета RPi
RUN mkdir -p /app/RPi && \
    cp /app/custom_gpio.py /app/RPi/GPIO.py && \
    echo 'from . import GPIO' > /app/RPi/__init__.py

# Добавляем путь к модулям в PYTHONPATH
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV PYTHONUNBUFFERED=1  
# Важно: отключаем буферизацию вывода

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 emulator
USER emulator

CMD ["python", "runner.py"]