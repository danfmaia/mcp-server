# Makefile for the MCP Server sub-project

# Use bash for more features like `source`
SHELL := /bin/bash

# Define the virtual environment directory
VENV_DIR := .venv

# Define Python interpreter path (uses python3 by default)
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip

# Define uv path explicitly using the path from the main project venv
UV := /home/danfmaia/_repos/career-agent/.venv/bin/uv

# Default target
.PHONY: help
help:
	@echo "MCP Server Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  install-dev  - Create venv and install all dependencies (runtime + test)"
	@echo "  sync         - Sync dependencies based on pyproject.toml (use install-dev for full setup)"
	@echo "  test         - Run pytest tests"
	@echo "  lint         - Run linters (TODO)"
	@echo "  run          - Run the MCP server"
	@echo "  clean        - Remove .venv and __pycache__"
	@echo ""

# Virtual environment setup and dependency installation
.PHONY: install-dev
install-dev: .venv/pyvenv.cfg ## Create venv and install all dependencies

.venv/pyvenv.cfg: pyproject.toml
	@echo "--> Creating virtual environment..."
	$(UV) venv
	@echo "--> Installing base dependencies..."
	source $(VENV_DIR)/bin/activate && $(UV) sync
	@echo "--> Installing test dependencies explicitly..."
	# Explicitly install test deps as uv sync --all-extras seems unreliable here
	source $(VENV_DIR)/bin/activate && $(UV) pip install pytest pytest-asyncio pytest-mock aiohttp aioresponses coverage pytest-cov ruff
	@touch .venv/pyvenv.cfg # Mark venv as configured by this target

# Basic sync target (may not install test deps reliably)
.PHONY: sync
sync:
	@echo "--> Syncing dependencies via uv sync..."
	source $(VENV_DIR)/bin/activate && $(UV) sync

# Testing
.PHONY: test
test: .venv/pyvenv.cfg ## Run tests with coverage
	@echo "--> Clearing pytest cache and running tests via coverage module..."
	# Explicitly use python -m coverage to invoke pytest
	export PATH="$(VENV_DIR)/bin:$$PATH" && python -m coverage run --source=src/mcp_server -m pytest tests/
	@echo "\n--> Generating coverage report..."
	# Show missing lines and fail if coverage is below 85%
	export PATH="$(VENV_DIR)/bin:$$PATH" && python -m coverage report -m --fail-under=85

# Linting
.PHONY: lint
lint: .venv/pyvenv.cfg ## Run linters (ruff)
	@echo "--> Running linters (ruff)..."
	# Check src and tests directories, attempt auto-fix
	export PATH="$(VENV_DIR)/bin:$$PATH" && ruff check src/mcp_server tests --fix

# Running the server
.PHONY: run
run: .venv/pyvenv.cfg ## Run the MCP server via stdio
	@echo "--> Running MCP Server via stdio..."
	export PYTHONUNBUFFERED=1 && $(VENV_DIR)/bin/python -m mcp_server.server

# Cleaning
.PHONY: clean
clean: ## Remove virtual environment and cache files
	@echo "--> Cleaning up..."
	rm -rf $(VENV_DIR)
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete 