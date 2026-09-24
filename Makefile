# dash's test entry points (WP-25).
#
# `make check' runs pytest under the Python Stata ships -- c(python_exec),
# which every Stata-built dashboard is rendered with -- and under the
# development interpreter, both strict (DASH_STRICT=1: a skip is not a pass,
# and a drifted environment stops the run before any test), then the
# certification suite through the console binary.  Any failure or unexpected
# skip makes it fail.  `make hooks' has `git push' run it first.
#
# Stata is run only through the console binary, in batch (CLAUDE.md rule 22).

PYTHON      ?= python3
STATA       ?= /usr/local/bin/stata-mp
PYTEST_ARGS ?= -q -p no:cacheprovider

.PHONY: help check test test-dev cert hooks

help:
	@echo "make check     make test, make test-dev and make cert, in that order"
	@echo "make test      pytest under Stata's Python, strict"
	@echo "make test-dev  pytest under the development interpreter ($(PYTHON)), strict"
	@echo "make cert      the certification suite, through the console binary"
	@echo "make hooks     have 'git push' run 'make check' first"

check: test test-dev cert

# Stata's Python is read from Stata itself each time: STATA_PYTHON overrides.
test:
	@py="$${STATA_PYTHON:-$$(STATA='$(STATA)' sh scripts/stata_python_exec.sh)}"; \
	if [ -z "$$py" ]; then \
	    echo "make test: could not read c(python_exec) from $(STATA)"; exit 1; \
	fi; \
	echo "pytest under Stata's Python: $$py"; \
	DASH_STRICT=1 DASH_BASELINE=stata "$$py" -m pytest test/ $(PYTEST_ARGS)

test-dev:
	@echo "pytest under the development interpreter: $(PYTHON)"
	@DASH_STRICT=1 DASH_BASELINE=dev $(PYTHON) -m pytest test/ $(PYTEST_ARGS)

cert:
	@STATA='$(STATA)' PYTHON='$(PYTHON)' sh scripts/run_cert_suite.sh

hooks:
	git config core.hooksPath scripts/git-hooks
	@echo "git push now runs 'make check' first; 'git push --no-verify' skips it."
