.PHONY: help up down logs ps seed train restart shell-api shell-web clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up:  ## Start all services in background
	docker compose -f infra/docker-compose.yml up -d --build
	@echo "Waiting for services to be healthy..."
	@sleep 10
	@docker compose -f infra/docker-compose.yml ps

down:  ## Stop all services
	docker compose -f infra/docker-compose.yml down

logs:  ## Tail logs (use CTRL-C to exit)
	docker compose -f infra/docker-compose.yml logs -f

ps:  ## List running services
	docker compose -f infra/docker-compose.yml ps

seed:  ## Seed demo data (tenant, users, sites, nodes, 7d readings)
	docker compose -f infra/docker-compose.yml exec api python /app/../infra/seed/seed.py

train:  ## Train ML model and persist to volume
	docker compose -f infra/docker-compose.yml exec api python -m app.ml.train

restart:  ## Restart a specific service (usage: make restart SVC=api)
	docker compose -f infra/docker-compose.yml restart $(SVC)

shell-api:  ## Open shell in api container
	docker compose -f infra/docker-compose.yml exec api /bin/bash

shell-web:  ## Open shell in web container
	docker compose -f infra/docker-compose.yml exec web /bin/sh

clean:  ## Stop services and remove volumes (DESTRUCTIVE)
	docker compose -f infra/docker-compose.yml down -v
	@echo "All data volumes removed."

init: up seed train  ## First-time setup: bring up, seed, train
	@echo ""
	@echo "================================================================"
	@echo "  Landslide EWS is ready!"
	@echo "  Web:     http://localhost:3000"
	@echo "  API:     http://localhost:8000"
	@echo "  API Doc: http://localhost:8000/docs"
	@echo "  MailHog: http://localhost:8025"
	@echo ""
	@echo "  Login: admin@acme.test / admin123"
	@echo "================================================================"
