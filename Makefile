.PHONY: test

test:
	pytest
	ruff check whostop tests
