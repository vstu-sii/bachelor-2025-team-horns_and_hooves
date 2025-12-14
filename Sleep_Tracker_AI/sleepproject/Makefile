.PHONY: help up down restart logs shell migrate createsuperuser test collectstatic clean stats app-logs db-logs redis-logs nginx-logs

# Вывод справки по доступным командам
help:
	@echo "\nДоступные команды:"
	@echo "  make up           - Запуск всех сервисов"
	@echo "  make down         - Остановка всех сервисов"
	@echo "  make restart      - Перезапуск сервисов"
	@echo "  make logs         - Просмотр логов всех сервисов"
	@echo "  make shell        - Открыть shell в контейнере web"
	@echo "  make migrate      - Применить миграции"
	@echo "  make createsuperuser - Создать суперпользователя"
	@echo "  make test         - Запуск тестов"
	@echo "  make collectstatic - Сбор статических файлов"
	@echo "  make clean        - Очистка (удаление всех данных и томов)"
	@echo "  make stats        - Просмотр использования ресурсов"
	@echo "  make app-logs     - Просмотр логов приложения"
	@echo "  make db-logs      - Просмотр логов базы данных"
	@echo "  make redis-logs   - Просмотр логов Redis"
	@echo "  make nginx-logs   - Просмотр логов Nginx"

# Запуск всех сервисов
up:
	docker-compose up -d

# Остановка всех сервисов
down:
	docker-compose down

# Перезапуск сервисов
restart:
	docker-compose restart

# Просмотр логов
logs:
	docker-compose logs -f

# Открыть shell в контейнере web
shell:
	docker-compose exec web bash

# Применить миграции
migrate:
	docker-compose exec web python manage.py migrate

# Создать суперпользователя
createsuperuser:
	docker-compose exec web python manage.py createsuperuser

# Запуск тестов
test:
	docker-compose exec web python manage.py test

# Сбор статических файлов
collectstatic:
	docker-compose exec web python manage.py collectstatic --no-input

# Очистка (осторожно! удалит все данные)
clean:
	docker-compose down -v
	rm -rf .coverage htmlcov/

# Просмотр использования ресурсов
stats:
	docker stats

# Просмотр логов приложения
app-logs:
	docker-compose logs -f web

# Просмотр логов базы данных
db-logs:
	docker-compose logs -f db

# Просмотр логов Redis
redis-logs:
	docker-compose logs -f redis

# Просмотр логов Nginx
nginx-logs:
	docker-compose logs -f nginx

# Инициализация проекта (первый запуск)
init: up migrate createsuperuser collectstatic
	@echo "\nПроект успешно инициализирован!"
	@echo "Доступные сервисы:"
	@echo "- Приложение: http://localhost:8000"
	@echo "- Админка: http://localhost:8000/admin"
	@echo "- Grafana: http://localhost:3000"

# Проверка состояния сервисов
status:
	docker-compose ps

# Пересборка и перезапуск сервисов
rebuild:
	docker-compose up -d --build

# Проверка синтаксиса Python-кода
lint:
	docker-compose exec web flake8 .
	docker-compose exec web black --check .

# Форматирование кода
format:
	docker-compose exec web black .
	docker-compose exec web isort .

# Создание миграций
makemigrations:
	docker-compose exec web python manage.py makemigrations

# Запуск Django shell
shell_plus:
	docker-compose exec web python manage.py shell_plus

# Запуск Celery worker
worker:
	docker-compose exec web celery -A sleepproject worker -l info

# Запуск Celery beat
beat:
	docker-compose exec web celery -A sleepproject beat -l info
