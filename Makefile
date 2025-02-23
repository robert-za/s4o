BACKEND_CONTAINER_NAME=app

build:
	docker build -t $(BACKEND_CONTAINER_NAME) .

check:
	docker run -t --rm --mount type=bind,source=.,target=/s4o $(BACKEND_CONTAINER_NAME) ruff check . --fix

format:
	docker run -t --rm --mount type=bind,source=.,target=/s4o $(BACKEND_CONTAINER_NAME) ruff format .

test:
	docker run -t --rm --mount type=bind,source=.,target=/s4o $(BACKEND_CONTAINER_NAME) python -m pytest /s4o/tests

commit:
	docker run --rm --mount type=bind,source=.,target=/s4o $(BACKEND_CONTAINER_NAME) bash -c "ruff check . --fix && ruff format ."

setup:
	bash -c "chmod +x setup.sh git-hooks/pre-commit git-hooks/pre-push && ./setup.sh"

mypy:
	docker run -t --rm --mount type=bind,source=.,target=/s4o $(BACKEND_CONTAINER_NAME) mypy .

final_boss: check format test mypy
