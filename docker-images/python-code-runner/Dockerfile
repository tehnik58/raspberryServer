FROM python:3.9-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя без привилегий root
RUN useradd -m -u 1000 user && chown -R user:user /home/user
USER user

# Установка Python библиотек (только разрешенные)
RUN pip install --no-cache-dir --user \
    RPi.GPIO \
    adafruit-circuitpython-servokit

# Создание директории для кода
WORKDIR /home/user/code

# Копирование заглушки RPi.GPIO и других эмуляторов
COPY --chown=user:user fake_rpi/ /home/user/.local/lib/python3.9/site-packages/fake_rpi/

# Копирование скрипта запуска
COPY --chown=user:user run_code.py /home/user/code/

# Установка переменной окружения для подмены модулей
ENV PYTHONPATH=/home/user/.local/lib/python3.9/site-packages

# Запуск скрипта выполнения
CMD ["python", "-u", "/home/user/code/run_code.py"]