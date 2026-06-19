init:
	pip install -r requirements.txt

test:
	pytest tests/ -v

lint:
	ruff check .

format:
	ruff format .

.PHONY: init test lint format
