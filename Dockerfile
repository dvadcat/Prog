FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для шрифтов и PDF
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Создание директории для базы данных
RUN mkdir -p instance

# Переменные окружения
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Порт приложения
EXPOSE 5000

# Запуск приложения
CMD ["python", "run.py"]
