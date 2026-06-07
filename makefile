SHELL := /bin/bash

init: .env .bootstrapped-pip .git/hooks/pre-commit
init-ci:
	touch .ignore-pre-commit
	make init

.bootstrapped-pip: requirements.txt
	pip install -r requirements.txt
	touch .bootstrapped-pip

.git/hooks/pre-commit:
	@if ! test -e ".ignore-pre-commit"; then \
  		pip install pre-commit; \
  		pre-commit install --install-hooks; \
	fi

.env:
	cp .env-example .env

test: init test-asserts
	python -m pytest tests
ci:
	make test
check: lint format-check test-asserts
lint:
	ruff check src/masoniteorm tests scripts
format: init
	ruff check --fix src/masoniteorm tests scripts
	ruff format src/masoniteorm tests scripts
format-check:
	ruff format --check src/masoniteorm tests scripts
test-asserts:
	python scripts/check_test_asserts.py
coverage:
	python -m pytest --cov-report term --cov-report xml --cov=src/masoniteorm tests/
	python -m coveralls
show:
	python -m pytest --cov-report term --cov-report html --cov=src/masoniteorm tests/
cov:
	python -m pytest --cov-report term --cov-report xml --cov=src/masoniteorm tests/
build:
	pip install build
	python -m build
