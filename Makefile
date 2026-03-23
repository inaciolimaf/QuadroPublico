.PHONY: dev down build test

dev:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

test:
	cd backend && pip install -r requirements-dev.txt -q && pytest -v
