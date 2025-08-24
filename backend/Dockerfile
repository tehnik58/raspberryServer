FROM python:3.9-slim

WORKDIR /app

# Устанавливаем системные зависимости включая Docker CLI
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Добавляем официальный GPG ключ Docker
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Добавляем репозиторий Docker
RUN echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Устанавливаем Docker CLI
RUN apt-get update && apt-get install -y \
    docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем все файлы бэкенда в рабочую директорию
COPY *.py ./

# Создаем директорию для фронтенда
RUN mkdir -p /app/frontend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]