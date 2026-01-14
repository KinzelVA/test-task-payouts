# Payout Requests Service (Django + DRF + Celery)

Небольшой REST-сервис для управления заявками на выплату средств.
Заявка создаётся через API и обрабатывается асинхронно в Celery (broker: Redis).
Реализована идемпотентность по `client_reference` и отмена заявки по правилам.

## Стек
- Python 3.10+
- Django 4.2 + Django REST Framework
- Celery + Redis
- PostgreSQL
- Docker / Docker Compose

---

## Быстрый старт (Docker)
Запуск проекта:

```bash
docker compose up --build
Сервис будет доступен на:

http://127.0.0.1:8000

Сущность: PayoutRequest
Поля

id — UUID

client_reference — внешний идентификатор клиента (используется для идемпотентности)

amount — сумма

currency — валюта (приводится к ISO-формату, например RUB)

destination — реквизиты/назначение выплаты

status — статус заявки

failure_reason — причина ошибки (если статус FAILED)

created_at, updated_at, processed_at — timestamps

Статусы

NEW — заявка создана, ожидает обработки

PROCESSING — заявка в обработке

PAID — успешно обработана

FAILED — обработка завершилась ошибкой

CANCELED — заявка отменена

API

Базовый префикс:
/api/v1

1) Создать заявку (идемпотентно)

POST /api/v1/payout-requests/

Ответы:

201 Created — заявка создана, отправлена на асинхронную обработку Celery

200 OK — заявка с таким client_reference уже существует, возвращаем существующую (новая Celery-задача не создаётся)

2) Получить список заявок

GET /api/v1/payout-requests/

3) Получить заявку по id

GET /api/v1/payout-requests/{id}/

4) Отменить заявку

POST /api/v1/payout-requests/{id}/cancel/

Правило:

отменить можно только NEW или PROCESSING

если PAID/FAILED/CANCELED → 400 Bad Request

Идемпотентность: создаём заявку через get_or_create по client_reference.
Celery-таска стартует только если запись действительно создана (created=True).

Защита от гонок: переход NEW -> PROCESSING выполняется атомарным UPDATE по условию статуса.

Cancel: выполняется условным UPDATE только для статусов NEW/PROCESSING.

## Запуск тестов

В Docker:

```bash
docker compose exec web python manage.py test -v 2
Локально (если нужно)
python src/manage.py test -v 2

idempotency по client_reference

async processing Celery

cancel only NEW/PROCESSING

tests included

## Частые команды

PowerShell (Windows):

```powershell
.\tasks.ps1 up
.\tasks.ps1 test
.\tasks.ps1 logs
.\tasks.ps1 down

“Endpoints”

GET /api/v1/payout-requests/

POST /api/v1/payout-requests/

GET /api/v1/payout-requests/{id}/

POST /api/v1/payout-requests/{id}/cancel/