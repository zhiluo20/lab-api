PYTHON ?= python3
VENV ?= .venv
ACTIVATE = . $(VENV)/bin/activate

.PHONY: help venv dev fmt lint type test run docker-build docker-up docker-down clean check

help:
	@echo "Available targets:"
	@echo "  make venv            # Create a local virtual environment"
	@echo "  make dev             # Install dependencies into the venv"
	@echo "  make fmt             # Format code with black"
	@echo "  make lint            # Run ruff and flake8"
	@echo "  make type            # Run mypy type checks"
	@echo "  make test            # Run pytest with coverage"
	@echo "  make run             # Start the Flask dev server"
	@echo "  make docker-build    # Build the Docker image"
	@echo "  make docker-up       # Start the docker-compose stack"
	@echo "  make docker-down     # Stop the stack and remove volumes"
	@echo "  make check           # Run fmt, lint, type, and tests"

venv:
	$(PYTHON) -m venv $(VENV)

dev: venv
	$(ACTIVATE) && pip install --upgrade pip
	$(ACTIVATE) && pip install -r requirements.txt

fmt:
	$(ACTIVATE) && black app tests

lint:
	$(ACTIVATE) && ruff check app tests
	$(ACTIVATE) && flake8 app tests

type:
	$(ACTIVATE) && mypy app

test:
	$(ACTIVATE) && pytest --cov=app --cov-report=term-missing

run:
	FLASK_APP=app.wsgi:app FLASK_ENV=development $(ACTIVATE) && flask run --reload

check: fmt lint type test

clean:
	rm -rf $(VENV) .mypy_cache .pytest_cache htmlcov

DOCKER_IMAGE ?= lab-api

docker-build:
	docker build -t $(DOCKER_IMAGE) .

docker-up:
	docker compose up -d

docker-down:
	docker compose down --remove-orphans

docker-clean:
	docker compose down --volumes --remove-orphans
