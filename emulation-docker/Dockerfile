FROM python:3.9-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем пакеты для эмуляции
RUN pip install requests
RUN pip install numpy
# Создаем директорию для состояний GPIO
RUN mkdir -p /app/gpio_states && chmod 777 /app/gpio_states

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

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 emulator
USER emulator

CMD ["python", "runner.py"]