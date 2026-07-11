.PHONY: install lint test clean docs run-nvda

install:
	pip install -e .[dev]
	pre-commit install

lint:
	ruff check src/ tests/
	mypy src/ tests/

test:
	pytest tests/ -v

run-nvda:
	valstudio run --ticker NVDA --scenario bull --output models/examples/sample_valuation_nvda.xlsx

docs:
	python scripts/make_docs.py

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
