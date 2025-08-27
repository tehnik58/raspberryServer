FROM python:3.9-slim
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем пакеты для эмуляции
RUN pip install requests

# Копируем кастомные файлы эмуляции
COPY custom_gpio.py .
COPY custom_components.py .
COPY custom_spi.py .
COPY custom_i2c.py .
COPY runner.py .
COPY execute.py .

# Делаем execute.py исполняемым
RUN chmod +x execute.py

# Создаем правильную структуру пакета RPi
RUN mkdir -p /app/RPi && \
    cp /app/custom_gpio.py /app/RPi/GPIO.py && \
    echo 'from . import GPIO' > /app/RPi/__init__.py

# Создаем структуру для spidev
RUN mkdir -p /app/spidev && \
    cp /app/custom_spi.py /app/spidev/__init__.py

# Создаем структуру для smbus и smbus2
RUN mkdir -p /app/smbus && \
    cp /app/custom_i2c.py /app/smbus/__init__.py && \
    mkdir -p /app/smbus2 && \
    cp /app/custom_i2c.py /app/smbus2/__init__.py

# Добавляем путь к модулям в PYTHONPATH
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV PYTHONUNBUFFERED=1

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 emulator
USER emulator

# Запускаем сервис в фоновом режиме
CMD ["python", "runner.py"]