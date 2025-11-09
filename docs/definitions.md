# Критерии DoR (Definition of Ready) и DoD (Definition of Done)

## Спринт 2: Проектирование архитектуры
### DoR (Готовность к началу спринта):
- Утверждены use-cases из Спринта 1.
- Команда ознакомилась с целями спринта.
- Роли распределены, задачи декомпозированы.

### DoD (Завершённость спринта):
- **SA/PO**:
  - Созданы документы: `requirements.md`, `c4-diagrams.md`, `roadmap.md`, `definitions.md`.
- **Fullstack**:
  - Готовы: `schema.sql`, `wireframes.figma`, `user-flows.miro`, `openapi.yaml`.
- **MLOps**:
  - Созданы: `docker-compose.dev.yml`, папка `.github/workflows/`, `monitoring/`, `infrastructure.md`.
- **AI Engineer**:
  - Созданы: `ml/requirements.md`, `data/`, `prompt_templates.py`, `baseline.py`, `baseline_report.md`.

## Спринт 3: Прототипирование MVP
### DoR:
- Утверждены архитектура и технические требования.
- Настроена базовая инфраструктура (docker-compose).

### DoD:
- **SA/PO**:
  - Обновлены: `requirements-v2.md`, `c4-actual.md`, `sprint4-plan.md`, `integration-report.md`.
- **Fullstack**:
  - Реализованы: каркас фронтенда, API, интеграция с БД и AI.
- **MLOps**:
  - Настроены: `docker-compose.yml`, Dockerfiles, CI/CD, Langfuse.
- **AI Engineer**:
  - Реализованы: baseline-модель, трассировка, эксперименты.

## Спринт 4: Production-инфраструктура
### DoR:
- Готов рабочий прототип.
- Утверждён MVP-scope.

### DoD:
- **SA/PO**:
  - Созданы: `mvp-scope.md`, `environments.md`, `quality-report.md`, обновлён `README.md`.
- **Fullstack**:
  - Реализованы все use-cases, написаны тесты, обработаны ошибки.
- **MLOps**:
  - Настроены: production-инфраструктура, мониторинг, алерты.
- **AI Engineer**:
  - Проведены A/B тесты, оптимизированы промпты, выполнено нагрузочное тестирование.

## Спринт 5: Тестирование и метрики
### DoR:
- Завершена реализация всех компонентов системы.

### DoD:
- **SA/PO**:
  - Созданы: `testing-report.md`, `requirements-v3.md`, `goals-analysis.md`, `improvements-plan.md`.
- **Fullstack**:
  - Подготовлены: `ux-testing-report.md`, тесты и отчёты, исправлены баги.
- **MLOps**:
  - Настроены: quality gates, дашборды Grafana, стратегия масштабирования.
- **AI Engineer**:
  - Проведены A/B тесты, собраны метрики, подготовлен финальный отчёт.

## Спринт 6: Demo Day
### DoR:
- Система полностью протестирована и стабильна.

### DoD:
- **Все роли**:
  - Проведена презентация проекта.
  - Продемонстрирована работа системы.
  - Даны ответы на вопросы экспертов.

## Спринт 7: Рецензирование
### DoR:
- Завершён Demo Day.

### DoD:
- **Все роли**:
  - Подготовлены отчёты по рецензированию.
  - Созданы гайды best practices.
  - Предоставлена обратная связь другим командам.
