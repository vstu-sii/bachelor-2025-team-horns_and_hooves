# Настройка окружений

## Организация раздельных окружений

### Development (Разработка)

```bash
# .env.development
DJANGO_SECRET_KEY=
BD_NAME=
BD_USER=
BD_PASSWORD=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
STATIC_ROOT=/app/static
MEDIA_ROOT=/app/media
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=http://localhost:3000
BASELINE_MAX_RETRIES=3
BASELINE_RETRY_DELAY=1.5
```

### Staging (Тестирование)

```bash
# .env.staging
DJANGO_SECRET_KEY=
BD_NAME=
BD_USER=
BD_PASSWORD=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
CELERY_BROKER_URL=redis://redis:6379/0
STATIC_ROOT=/app/static
MEDIA_ROOT=/app/media
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=http://localhost:3000
BASELINE_MAX_RETRIES=3
BASELINE_RETRY_DELAY=1.5
```

### Production (Продакшен)

```bash
# .env.production
DJANGO_SECRET_KEY=
BD_NAME=
BD_USER=
BD_PASSWORD=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
STATIC_ROOT=/app/static
MEDIA_ROOT=/app/media
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=http://localhost:3000
BASELINE_MAX_RETRIES=3
BASELINE_RETRY_DELAY=1.5
```

## Управление переменными окружения

### Критические переменные

```bash
DJANGO_SECRET_KEY=
BD_NAME=
BD_USER=
BD_PASSWORD=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
STATIC_ROOT=/app/static
MEDIA_ROOT=/app/media
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=http://localhost:3000
BASELINE_MAX_RETRIES=3
BASELINE_RETRY_DELAY=1.5
```

## Стратегия ротации секретов

| Секрет | Периодичность | Метод ротации |
|--------|---------------|---------------|
| DJANGO_SECRET_KEY | Ежеквартально | Генерация нового, постепенная замена |
| БД пароли | Полугодично | Создание нового пользователя, миграция |
| API ключи | По необходимости | Через панели управления сервисов |



## 4. Планы резервного копирования и восстановления

### Ежедневное бэкапирование

```yaml
services:
  db_backup:
    image: postgres:13
    volumes:
      - ./backups:/backups
    command: |
      bash -c "
        pg_dump -h postgres -U $${DB_USER} $${DB_NAME} > /backups/backup-$$(date +%Y-%m-%d).sql
        find /backups -name '*.sql' -mtime +7 -delete
      "
    environment:
      - DB_USER=
      - DB_NAME=
      - BD_PASSWORD=
    depends_on:
      - postgres
```

### Процесс восстановления

```bash

docker-compose exec postgres psql -U postgres -d bd_sleepstatistic -f /backups/backup-2024-01-15.sql


tar -xzf backups/media-2024-01-15.tar.gz -C /app/media/
```
