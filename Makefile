.PHONY: help install run-app run-worker test lint format clean docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  install      - Install dependencies"
	@echo "  run-app      - Run the FastAPI application"
	@echo "  run-worker   - Run the background worker"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  clean        - Clean cache and temporary files"
	@echo "  docker-build - Build Docker containers"
	@echo "  docker-up    - Start Docker containers"
	@echo "  docker-down  - Stop Docker containers"

install:
	pip install -r requirements.txt

run-app:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-worker:
	arq app.worker.WorkerSettings

test:
	pytest tests/ -v

lint:
	ruff check app/

format:
	ruff format app/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Database commands
db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

db-revision:
	alembic revision --autogenerate -m "$(message)"

# Development setup
setup-dev: install
	cp .env.example .env
	@echo "Please edit .env file with your configuration"

# Create admin user
create-admin:
	python -c "from app.scripts.create_admin import create_admin_user; create_admin_user()" 