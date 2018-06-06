PYTHON = python
PIP = $(PYTHON) -m pip
PYTEST = $(PYTHON) -m pytest

all: install test

install:
	@echo "---- Installing ---- "
	@$(PIP) install -e .[test]

test:
	@echo "---- Running tests ---- "
	@$(PYTEST) -v .

.PHONY: all install test
