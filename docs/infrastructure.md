# Документация проекта: sleep-statistic-django

> Веб‑приложение на Django для персональной рекомендации по улучшению качества сна с Celery, Redis, PostgreSQL, Nginx, Ollama и Gemeni FLASH 2. Всё работает через Docker Compose; Всё работает через Docker + GitHub Actions + Prometheus/Grafana для мониторинга.

---

## 1. Запуск локального окружения

### Предварительные требования

- Docker Desktop (или Docker Engine + Compose на Linux)
- Git
- Опционально: VS Code

---

### Быстрый старт

```bash
# Клонируйте репозиторий
git clone https://github.com/<ваш-юзернейм>/sleep-statistic-django.git
cd sleep-statistic-django

# Создайте .env (пример ниже) и запустите
docker compose -f docker-compose.dev.yml up --build
```

---

### Что запускается

- Django + Gunicorn → http://localhost:8000
- Nginx → http://localhost:80 (раздача статики/медиа и прокси на Django)
- PostgreSQL → доступно внутри сети
- Redis → доступно внутри сети
- Celery worker → обработка фоновых задач
- Celery beat → расписание периодических задач
- Ollama → http://localhost:11434 или внутри сети

---

### Пример .env

```env
# Django
DJANGO_SECRET_KEY=

BD_NAME=
BD_USER=
BD_PASSWORD=

EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

CELERY_BROKER_URL=
```

---

### Как работать с кодом

- В режиме dev используется bind‑mount: изменения в проекте видны в контейнере сразу после перезапуска сервиса.
- Быстрая пересборка:
  ```bash
  docker compose -f docker-compose.dev.yml down && docker compose -f docker-compose.dev.yml up --build
  ```
- Войти в контейнер:
  ```bash
  docker exec -it <имя_контейнера> bash
  ```

---

## 2. Troubleshooting guide

### Django не видит базу данных

- Проверьте DATABASE_URL в .env, имя сервиса — db:
  - Формат: postgres://USER:PASSWORD@db:5432/DB
- Убедитесь, что db и web в одной Docker‑сети.
- Добавьте healthcheck для Postgres и depends_on: condition=service_healthy.


### Nginx отдаёт 404 на статику

- Проверьте STATIC_ROOT=/app/static и MEDIA_ROOT=/app/media в settings.py.
- Убедитесь, что выполнен collectstatic:
  ```bash
  docker compose exec web python manage.py collectstatic --no-input
  ```
- Проверьте пути в nginx.conf (location для /static/ и /media/).

### Celery не подключается к брокеру

- Убедитесь в CELERY_BROKER_URL=redis://redis:6379/0.
- Проверьте, что сервис redis в сети и живой (healthcheck).
- Посмотрите логи:
  ```bash
  docker compose logs celery
  ```

### Gunicorn падает по таймауту при импорте CSV

- Увеличьте timeout и количество воркеров:
  ```bash
  gunicorn sleepproject.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 2 --timeout 120
  ```

### Ollama не запускается

- Убедитесь, что директория ./.ollama_data существует и доступна.
- Логи:
  ```bash
  docker logs ollama
  ```
- Для GPU: включите секцию deploy с nvidia и установите драйверы на хосте.

### GitHub Actions падает

**Проверьте:**

- Синтаксис YAML в `.github/workflows/`.
- Установлены ли нужные версии Node.js в workflow.
- Правильно ли указаны команды `npm install`, `npm test`.

**Решение:**

1. Убедитесь, что workflow‑файл корректен и проходит проверку синтаксиса.
2. В блоке `uses: actions/setup-node@v4` задайте поддерживаемую версию Node.js (например, `20.x`).
3. Проверьте, что команды сборки и тестирования совпадают с теми, что используются локально (`npm ci`, `npm run build`, `npm test`).
4. При необходимости пересоздайте lock‑файл (`package-lock.json`) и закоммитьте его в репозиторий.

---

## 3. Архитектура инфраструктуры

- Backend (Django + Gunicorn) — HTML, бизнес‑логика анализа сна.
- PostgreSQL — хранилище данных, миграции через Django.
- Redis — брокер для Celery и кэш для Django.
- Celery worker — фоновая обработка: анализ, импорт, расчёты.
- Celery beat — расписание: уведомления.
- Nginx — статика/медиа, reverse proxy на web.
- Ollama — локальный LLM‑движок для RAG/ассистента.
- Langfuse — трассировка, логирование и оценка вызовов LLM (observability для ML).
- Prometheus — сбор метрик производительности и состояния сервисов.
- Grafana — визуализация метрик из Prometheus, дашборды для мониторинга.
- Docker Compose — orchestrator для запуска всех сервисов локально.
- GitHub Actions — CI/CD для автоматизации сборки, тестирования и деплоя.

---
## 4. Cheat sheet для команды

### Docker Compose

| Команда | Описание |
|--------|----------|
| docker compose up | Запустить все сервисы |
| docker compose up --build | Пересобрать и запустить |
| docker compose down | Остановить и удалить контейнеры |
| docker compose logs <service> | Логи сервиса |
| docker compose exec <service> bash | Шелл внутри контейнера |

### Git — основные команды

| Команда | Описание |
|---------|----------|
| `git clone <repo-url>` | Клонировать репозиторий |
| `git checkout -b feat/<название-фичи>` | Создать новую ветку для фичи |
| `git status` | Проверить состояние рабочей директории |
| `git add .` | Добавить все изменения в индекс |
| `git commit -m "feat: описание изменений"` | Сделать коммит |
| `git push origin feat/<название-фичи>` | Отправить ветку на GitHub |
| `git fetch && git rebase origin/main` | Обновить ветку с `main` |
| `git pull` | Получить последние изменения |
| `git merge <branch>` | Слить ветку в текущую |
| `git log --oneline --graph` | Просмотреть историю коммитов |

---

### Типы коммитов (Conventional Commits)

| Тип | Описание |
|-----|----------|
| `feat` | Новая функциональность |
| `fix` | Исправление бага |
| `docs` | Изменения в документации |
| `style` | Форматирование, стили (без изменения логики) |
| `refactor` | Рефакторинг кода |
| `test` | Добавление/изменение тестов |
| `chore` | Служебные изменения (обновление зависимостей, конфигов) |

---

### Примеры сообщений коммитов

- `feat: добавлен импорт CSV для сна`
- `fix: исправлена ошибка расчёта хронотипа`
- `docs: обновлена инструкция по запуску`
- `style: форматирование кода в models.py`
- `refactor: вынес логику анализа сна в отдельный модуль`
- `test: добавлены unit-тесты для SleepRecord`
- `chore: обновлены зависимости poetry`

---

### Django

- **Миграции:**
  ```bash
  docker compose exec web python manage.py migrate
  ```
- **Сбор статики:**
  ```bash
  docker compose exec web python manage.py collectstatic --no-input
  ```
- **Создать суперпользователя:**
  ```bash
  docker compose exec web python manage.py createsuperuser
  ```

### Celery

- **Запуск (внутри контейнера):**
  ```bash
  celery -A sleepproject worker --loglevel=info --concurrency=4 --prefetch-multiplier=1
  ```
- **Beat (расписание):**
  ```bash
  celery -A sleepproject beat --loglevel=info
  ```

### Ссылки (dev)

| Сервис | URL |
|--------|-----|
| Django (web) | http://localhost:8000 |
| Nginx | http://localhost:80 |
| Ollama API | http://localhost:11434 |

---

## 5. Рекомендации по конфигурации

### Compose: безопасность и готовность

- Не пробрасывайте порты db и redis наружу в продакшене.
- Добавьте healthcheck:
  - Postgres:
    ```yaml
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $POSTGRES_USER -d $POSTGRES_DB"]
      interval: 5s
      timeout: 5s
      retries: 10
    ```
  - Redis:
    ```yaml
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10
    ```
- depends_on с condition: service_healthy для web, celery, beat.
- Определите единую приватную сеть (например, devserver) и подключите все сервисы.

### Gunicorn

- Рекомендуемые параметры:
  ```bash
  --workers 3 --threads 2 --timeout 120 --access-logfile - --error-logfile -
  ```

### Django settings

- **STATIC_ROOT**=/app/static
- **MEDIA_ROOT**=/app/media
- **DATABASE_URL**=postgres://…@db:5432/…
- **CACHES** с Redis (cache URL)
- **CELERY**: broker_url, result_backend, task_serializer, accept_content
- **SECURITY**: ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, заголовки для продакшена
- **TIME_ZONE**: Europe/Warsaw

### Prod vs Dev

- Dev: bind‑mount кода `.:/app` для быстрой разработки.
- Prod: без bind‑mount; используйте сборку образа и named volumes только для данных (static, media, postgres, redis). Прокси‑доступ наружу — только через Nginx, web не публикуйте.

### Nginx

- Отдавайте `/app/static` и `/app/media`, остальное проксируйте на `web:8000`.
- Для продакшена — HTTPS (Caddy/Traefik/Certbot), HSTS, gzip.

---

## 6. Пример GitHub Actions

```yaml
### Пример workflow для Node.js

name: Node.js CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Use Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20.x'
      - run: npm ci
      - run: npm run build --if-present
      - run: npm test

```