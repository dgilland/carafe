.PHONY: build clean clean-env clean-files venv install test test-full test-tox lint pep8 pylint release travisci-install travisci-test

##
# Variables
##

ENV_NAME = env
ENV_ACT = . env/bin/activate;
PIP = $(ENV_NAME)/bin/pip
PYTEST_ARGS = --doctest-modules -v -s
PYTEST_TARGET = carafe tests
COVERAGE_ARGS = --cov-config setup.cfg --cov-report term-missing --cov
COVERAGE_TARGET = carafe

##
# Targets
##

build: clean venv install

clean: clean-env clean-files

clean-env:
	rm -rf $(ENV_NAME)

clean-files:
	rm -rf .tox
	rm -rf .coverage
	find . -name \*.pyc -type f -delete
	find . -name \*.test.db -type f -delete
	find . -depth -name __pycache__ -type d -exec rm -rf {} \;
	rm -rf dist *.egg* build

venv:
	virtualenv $(ENV_NAME) --no-site-packages

install:
	rm -rf $(ENV_NAME)
	virtualenv $(ENV_NAME)
	$(PIP) install -r requirements.txt

clean-install: clean-env venv install

test:
	$(ENV_ACT) py.test $(PYTEST_ARGS) $(COVERAGE_ARGS) $(COVERAGE_TARGET) $(PYTEST_TARGET)

test-full: test-tox

test-tox:
	rm -rf .tox
	$(ENV_ACT) tox

# linting
lint: pylint pep8

pep8:
	$(ENV_ACT) pep8 $(PYTEST_TARGET)

pylint:
	$(ENV_ACT) pylint $(COVERAGE_TARGET)


release:
	$(ENV_ACT) python setup.py sdist bdist_wheel
	$(ENV_ACT) twine upload dist/*
	rm -rf dist *.egg* build

##
# TravisCI
##

travisci-install:
	pip install -r requirements.txt

travisci-test:
	py.test $(PYTEST_ARGS) $(COVERAGE_ARGS) $(COVERAGE_TARGET) $(PYTEST_TARGET)