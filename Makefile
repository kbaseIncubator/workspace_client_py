.PHONY: test

test:
	PYTHONPATH=src poetry run python -m unittest discover src/test
