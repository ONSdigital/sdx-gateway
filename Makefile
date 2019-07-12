.PHONY: build test

build:
	pip3 install -r requirements.txt

test: build
	pip3 install -r test_requirements.txt*
	pytest -v --capture=no --cov-report term-missing --cov=app tests/

