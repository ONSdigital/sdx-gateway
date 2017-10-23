.PHONY: build test

build:
	pip3 install -r requirements.txt

test: build
	pip3 install -r test_requirements.txt*
	pytest tests/
