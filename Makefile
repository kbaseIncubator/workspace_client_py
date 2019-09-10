.PHONY: test

test:
	PYTHONPATH=src python -m unittest discover src/test
