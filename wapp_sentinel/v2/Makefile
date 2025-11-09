.PHONY: help build up down logs restart clean test migrate shell db-shell

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## View logs from all services
	docker-compose logs -f

logs-api: ## View API logs
	docker-compose logs -f api

logs-ai: ## View AI Agent logs
	docker-compose logs -f ai_agent_worker

logs-rabbitmq: ## View RabbitMQ Worker logs
	docker-compose logs -f rabbitmq_worker

logs-processor: ## View Order Processor logs
	docker-compose logs -f order_processor_worker

restart: ## Restart all services
	docker-compose restart

restart-api: ## Restart API service
	docker-compose restart api

restart-ai: ## Restart AI Agent
	docker-compose restart ai_agent_worker

restart-rabbitmq: ## Restart RabbitMQ Worker
	docker-compose restart rabbitmq_worker

restart-processor: ## Restart Order Processor
	docker-compose restart order_processor_worker

clean: ## Stop services and remove volumes
	docker-compose down -v

ps: ## Show running containers
	docker-compose ps

migrate: ## Run database migrations
	docker-compose exec api alembic upgrade head

migrate-create: ## Create new migration (use NAME=migration_name)
	docker-compose exec api alembic revision --autogenerate -m "$(NAME)"

shell: ## Open shell in API container
	docker-compose exec api bash

shell-ai: ## Open shell in AI Agent container
	docker-compose exec ai_agent_worker bash

shell-rabbitmq: ## Open shell in RabbitMQ Worker container
	docker-compose exec rabbitmq_worker bash

shell-processor: ## Open shell in Order Processor container
	docker-compose exec order_processor_worker bash

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d napoleon_db

db-backup: ## Backup database
	docker-compose exec postgres pg_dump -U postgres napoleon_db > backup_$$(date +%Y%m%d_%H%M%S).sql

test: ## Run tests (if available)
	docker-compose exec api pytest

dev: ## Start services in development mode
	docker-compose up

prod: ## Start services in production mode
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

rebuild: down build up ## Rebuild and restart all services

rebuild-api: ## Rebuild and restart API
	docker-compose build api
	docker-compose up -d api

rebuild-ai: ## Rebuild and restart AI Agent
	docker-compose build ai_agent_worker
	docker-compose up -d ai_agent_worker

rebuild-rabbitmq: ## Rebuild and restart RabbitMQ Worker
	docker-compose build rabbitmq_worker
	docker-compose up -d rabbitmq_worker

rebuild-processor: ## Rebuild and restart Order Processor
	docker-compose build order_processor_worker
	docker-compose up -d order_processor_worker

stats: ## Show container resource usage
	docker stats --no-stream

prune: ## Remove unused Docker resources
	docker system prune -f

prune-all: ## Remove all unused Docker resources including volumes
	docker system prune -af --volumes
