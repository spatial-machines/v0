.PHONY: demo verify test test-quick clean wiki-count wiki-gaps wiki-links validate-maps lint benchmark-audit help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

demo: ## Run a 2-minute demo analysis on bundled Census data (no API keys needed)
	python scripts/demo.py

verify: ## Verify repo integrity (scripts compile, wiki count, no broken references)
	@python -m py_compile scripts/core/validate_cartography.py
	@python -m py_compile scripts/core/validate_benchmark_batch.py
	@python -m py_compile scripts/core/handoff_utils.py
	@python -m py_compile scripts/core/run_peer_review.py
	@echo "Core scripts compile OK."
	@echo "Wiki pages: $$(find docs/wiki -name '*.md' | wc -l)"
	@echo "Agent roles: $$(ls -d agents/*/SOUL.md | wc -l)"

test: ## Run the test suite
	python -m pytest tests/ -v

test-quick: ## Run tests without slow/integration markers
	python -m pytest tests/ -v -m "not slow"

wiki-count: ## Count wiki pages by category
	@echo "Domains:      $$(ls docs/wiki/domains/*.md 2>/dev/null | wc -l)"
	@echo "Workflows:    $$(ls docs/wiki/workflows/*.md 2>/dev/null | wc -l)"
	@echo "QA review:    $$(ls docs/wiki/qa-review/*.md 2>/dev/null | wc -l)"
	@echo "Data sources: $$(ls docs/wiki/data-sources/*.md 2>/dev/null | wc -l)"
	@echo "Toolkits:     $$(ls docs/wiki/toolkits/*.md 2>/dev/null | wc -l)"
	@echo "Standards:    $$(ls docs/wiki/standards/*.md 2>/dev/null | wc -l)"
	@echo "---"
	@echo "Total:        $$(find docs/wiki -name '*.md' | wc -l)"

wiki-gaps: ## Check for (planned) annotations in wiki
	@grep -rn "(planned)" docs/wiki/ || echo "No (planned) annotations found."

wiki-links: ## List all cross-references in wiki pages (for future link validation)
	@grep -roh '`[a-z-]*/[A-Z_]*\.md`' docs/wiki/ | sort | uniq -c | sort -rn | head -30

validate-maps: ## Validate all map PNGs in a project (usage: make validate-maps PROJECT=my-analysis)
	python scripts/core/validate_cartography.py --input-dir analyses/$(PROJECT)/outputs/maps/

lint: ## Run basic Python linting on core scripts
	@for f in scripts/core/*.py; do python -m py_compile "$$f" || exit 1; done
	@echo "All core scripts compile OK."

benchmark-audit: ## Validate benchmark batch consistency (usage: make benchmark-audit BENCHMARK_ROOT=analyses/benchmark-day1 SUMMARY_CSV=summary/scores.csv)
	python scripts/core/validate_benchmark_batch.py --benchmark-root $(BENCHMARK_ROOT) --summary-csv $(BENCHMARK_ROOT)/$(SUMMARY_CSV)

clean: ## Remove Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cache cleaned."
