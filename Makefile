.PHONY: up down build logs ps test shell lint

up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

test:
	docker compose exec web python manage.py test -v 2

shell:
	docker compose exec web python manage.py shell

lint:
	docker compose exec web python -m compileall .
