.PHONY: build test

build:
	pip install -r requirements.txt

start:
	python run.py

test: build
	pip install -r test_requirements.txt*
	pytest -v --capture=no --cov-report term-missing --cov=app tests/

