.PHONY: help install clean test tox bump act-check ci-check quick
.DEFAULT_GOAL := help

# Colors for output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RESET := \033[0m

help: ## Show available targets
	@echo "$(BLUE)Development workflow targets:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install project in development mode
	@echo "$(BLUE)Installing project...$(RESET)"
	uv pip install --system -e .
	@echo "$(GREEN)Project installed$(RESET)"

clean: ## Clean up build artifacts and caches
	@echo "$(BLUE)Cleaning up project...$(RESET)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "*.pyo" -delete 2>/dev/null || true
	@find . -name ".coverage" -delete 2>/dev/null || true
	@rm -rf dist/ build/ *.egg-info/ htmlcov/ 2>/dev/null || true
	@echo "$(GREEN)Cleanup completed$(RESET)"

test: ## Run pytest tests
	@echo "$(BLUE)Running pytest...$(RESET)"
	uv run pytest tests/ --import-mode importlib -v
	@echo "$(GREEN)Tests completed$(RESET)"

tox: ## Run tox environments
	@echo "$(BLUE)Running tox...$(RESET)"
	uv run tox
	@echo "$(GREEN)Tox completed$(RESET)"

bump: ## Bump version with commitizen
	@echo "$(BLUE)Bumping version with commitizen...$(RESET)"
	uv run cz bump
	@echo "$(GREEN)Version bumped$(RESET)"

act-check: ## Dry-run GitHub Actions with act
	@echo "$(BLUE)Testing GitHub workflow with act...$(RESET)"
	@if command -v act >/dev/null 2>&1; then \
		act -j test --dryrun --container-architecture linux/amd64; \
		echo "$(GREEN)Act check completed$(RESET)"; \
	else \
		echo "$(RED)Error: 'act' is not installed$(RESET)"; \
		echo "$(YELLOW)Install with: brew install act$(RESET)"; \
		exit 1; \
	fi

ci-check: ## Simulate CI pipeline locally (test + tox)
	@echo "$(BLUE)Running CI simulation...$(RESET)"
	$(MAKE) test
	$(MAKE) tox
	@echo "$(GREEN)CI check completed$(RESET)"

quick: ## Quick workflow: clean, install, test, tox
	@echo "$(BLUE)Running quick workflow...$(RESET)"
	$(MAKE) clean
	$(MAKE) install
	$(MAKE) test
	$(MAKE) tox
	@echo "$(GREEN)Quick workflow completed$(RESET)"
