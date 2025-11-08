# Используем официальный облегчённый образ Python 3.12
FROM python:3.12-slim

# Настройки окружения:
# - PYTHONDONTWRITEBYTECODE=1 отключает создание .pyc файлов
# - PYTHONUNBUFFERED=1 заставляет Python писать логи сразу (без буфера)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем системные зависимости:
# - build-essential: инструменты для сборки (gcc, make и т.д.)
# - libpq-dev: библиотеки для работы с PostgreSQL (нужны для psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория внутри контейнера
WORKDIR /app

# Устанавливаем Poetry для управления зависимостями Python
RUN pip install --no-cache-dir poetry

# Копируем файлы зависимостей (pyproject.toml и poetry.lock) внутрь контейнера
# Это позволяет Docker кэшировать слой с зависимостями и не пересобирать его при каждом изменении кода
COPY pyproject.toml poetry.lock* /app/

# Устанавливаем зависимости проекта через Poetry
# --no-root означает, что сам проект (.) не будет устанавливаться как пакет
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Копируем весь проект внутрь контейнера
COPY . .

# Создаём необходимые директории для работы приложения:
# - /app/static: для статических файлов Django (CSS, JS, изображения)
# - /app/media: для временного хранения csv
# - /app/logs: для логов приложения
# - /root/.olamma: директория для моделей Ollama
RUN mkdir -p /app/static \
    && mkdir -p /app/media \
    && mkdir -p /app/logs \
    && mkdir -p /root/.ollama

# Создаём непривилегированного пользователя appuser и назначаем ему права на директории
RUN useradd -m appuser && chown -R appuser:appuser /app /root/.ollama
USER appuser

# Открываем порт 8000 (Django/Gunicorn будет слушать на нём)
EXPOSE 8000
