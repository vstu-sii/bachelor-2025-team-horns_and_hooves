# Документация по приложению для отслеживания сна

## Технический стек

### Бэкенд
- **Python 3.10+**
- **Django 4.2.11** - Веб-фреймворк
- **Celery** - Асинхронная очередь задач
- **Redis** - Брокер сообщений и кеш
- **PostgreSQL** - База данных
- **Gunicorn** - HTTP-сервер WSGI 

### Фронтенд
- **HTML5, CSS3, JavaScript**
- **Bootstrap 5** - Адаптивный дизайн
- **Highcharts.js** - Интерактивная визуализация данных
- **jQuery** - Манипуляции с DOM и AJAX

### Инфраструктура
- **Docker** - Контейнеризация
- **Kubernetes** - Оркестрация контейнеров
- **Prometheus** - Мониторинг
- **Grafana** - Визуализация метрик
- **Loki** - Централизованное логирование

## Структура проекта

```
sleepproject/
├── .github/                  # Конфигурации и рабочие процессы GitHub
├── .ollama_data/             # Данные и конфигурации моделей Ollama
├── grafana/                  # Дашборды и конфигурация Grafana
├── htmlcov/                  # Отчеты о покрытии тестами
├── k8s/                      # Конфигурации Kubernetes
│   ├── celery-beat-deployment.yaml
│   ├── celery-deployment.yaml
│   ├── clickhouse-*.yaml     # Конфигурации ClickHouse
│   ├── db-*.yaml             # Конфигурации основной БД
│   ├── env-configmap.yaml    # Конфигурация переменных окружения
│   ├── grafana-*.yaml        # Конфигурации Grafana
│   ├── loki-*.yaml           # Конфигурации Loki
│   ├── minio-*.yaml          # Конфигурации MinIO
│   ├── nginx-*.yaml          # Конфигурации Nginx
│   ├── ollama-*.yaml         # Конфигурации Ollama
│   ├── prometheus-*.yaml     # Конфигурации Prometheus
│   ├── promtail-*.yaml       # Конфигурации Promtail
│   ├── redis-*.yaml          # Конфигурации Redis
│   └── web-*.yaml            # Конфигурации веб-приложения
├── loki/                     # Конфигурация системы логирования Loki
├── nginx/                    # Конфигурация веб-сервера Nginx
├── prometheus/               # Конфигурация мониторинга Prometheus
├── qdrant_storage/           # Хранилище для векторной БД Qdrant
├── sleep_articles/           # Статьи и контент о сне
├── sleep_tracking_app/       # Основное приложение Django
│   ├── migrations/           # Миграции базы данных
│   ├── prompts/              # Шаблоны и конфигурации AI-промптов
│   │   ├── __init__.py
│   │   ├── baseline.py      # Базовые конфигурации промптов
│   │   └── prompts_templates.py  # Шаблоны для AI-промптов
│   ├── sleep_statistic/      # Логика анализа и статистики сна
│   ├── static/               # Статические файлы (CSS, JS, изображения)
│   ├── templates/            # HTML-шаблоны
│   ├── tests/                # Директория с тестами
│   ├── admin.py              # Конфигурация административной панели
│   ├── apps.py               # Конфигурация приложения
│   ├── csv_data_extraction.py # Утилиты импорта/экспорта CSV
│   ├── forms.py              # Определения форм
│   ├── models.py             # Модели базы данных
│   ├── tasks.py              # Асинхронные задачи Celery
│   ├── urls.py               # Маршрутизация URL
│   └── views.py              # Обработчики запросов
├── sleepproject/             # Конфигурация проекта
│   ├── __init__.py
│   ├── asgi.py              # Конфигурация ASGI
│   ├── settings.py          # Настройки Django
│   ├── urls.py             # Корневая конфигурация URL
│   └── wsgi.py             # Конфигурация WSGI

# Основные конфигурационные файлы
├── .env                     # Переменные окружения
├── .gitignore
├── .coverage               # Данные о покрытии тестами
├── celerybeat-schedule.*    # Файлы расписания Celery Beat
├── docker-compose.yml       # Основная конфигурация Docker Compose
├── docker-compose-resolved.yml  # Резолвленная версия docker-compose
├── Dockerfile               # Конфигурация Docker для веб-приложения
├── infrastructure.md        # Документация по инфраструктуре
├── loki-config.yml          # Конфигурация Loki
├── Makefile                 # Утилитарные команды
├── manage.py                # Скрипт управления Django
├── poetry.lock             # Файл блокировки Poetry
├── prometheus.yml          # Конфигурация Prometheus
├── promtail-config.yaml    # Конфигурация Promtail
└── pyproject.toml          # Зависимости и конфигурация проекта
```

## Модели данных

### UserData
Хранит дополнительную информацию о пользователе:
- Дата рождения
- Вес и рост
- Пол
- Уровень активности

### SleepRecord
Отслеживает отдельные сеансы сна:
- Время начала и окончания сна
- Продолжительность фаз сна (легкий, глубокий, REM)
- Показатели частоты сердечных сокращений
- Периоды бодрствования
- Данные с устройств

### SleepStatistics
Агрегированный анализ сна:
- Эффективность сна
- Индекс фрагментации сна
- Расход калорий
- Оценка качества сна

## Развертывание

### Требования
- Docker 20.10+
- Docker Compose 2.0+
- kubectl (для Kubernetes)
- Доступ к кластеру Kubernetes (опционально)

### Развертывание с помощью Docker Compose

1. Клонируйте репозиторий:
   ```bash
   git clone <repository-url>
   cd Web-sleep-app/sleepproject
   ```

2. Настройте переменные окружения:
   ```bash
   cp .env.example .env
   ```

3. Запустите приложение:
   ```bash
   docker-compose up -d --build
   ```

4. Примените миграции:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. Создайте суперпользователя:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

### Развертывание в Kubernetes

1. Создайте неймспейс:
   ```bash
   kubectl create namespace sleep-app
   ```

2. Примените конфигурации:
   ```bash
   kubectl apply -f k8s/
   ```

3. Проверьте статус развертывания:
   ```bash
   kubectl get all -n sleep-app
   ```

## Мониторинг

Доступ к инструментам мониторинга:
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100

