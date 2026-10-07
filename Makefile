# dash's test entry points (WP-25).
#
# `make check' runs pytest under the Python Stata ships -- c(python_exec),
# which every Stata-built dashboard is rendered with -- and under the
# development interpreter, both strict (DASH_STRICT=1: a skip is not a pass,
# and a drifted environment stops the run before any test), then the
# certification suite through the console binary.  Any failure or unexpected
# skip makes it fail.  `make hooks' has `git push' run it first.
#
# Stata is run only through the console binary, in batch, started by scripts/stata_batch.sh.

PYTHON      ?= python3
STATA_BIN   ?= /usr/local/bin/stata-mp
PYTEST_ARGS ?= -q -p no:cacheprovider

ifeq ($(origin STATA),command line)
$(error STATA was renamed STATA_BIN (WP-30); run make $(MAKECMDGOALS) STATA_BIN=$(STATA))
endif

.PHONY: help check test test-dev test-floor cert gate release hooks

help:
	@echo "make check     make test, make test-dev and make cert, in that order"
	@echo "make test      pytest under Stata's Python, strict"
	@echo "make test-dev  pytest under the development interpreter ($(PYTHON)), strict"
	@echo "make test-floor  one floor-matrix leg, run by hand (not part of make gate): FLOOR_VENV=<dir> FLOOR_BASELINE=<name>"
	@echo "make cert      the certification suite, through the console binary"
	@echo "make gate      net install, then every example and scheme from the install"
	@echo "make release   make check, then make gate"
	@echo "make hooks     have 'git push' run 'make check' first"
	@echo "STATA_BIN=<path> names the console Stata (default /usr/local/bin/stata-mp); STATA_ARCH=auto|none|arm64|x86_64"

check: test test-dev cert

# Stata's Python is read from Stata itself each time: STATA_PYTHON overrides.
test:
	@py="$${STATA_PYTHON:-$$(STATA_BIN='$(STATA_BIN)' sh scripts/stata_python_exec.sh)}"; \
	if [ -z "$$py" ]; then \
	    echo "make test: could not read c(python_exec) from $(STATA_BIN)"; exit 1; \
	fi; \
	echo "pytest under Stata's Python: $$py"; \
	DASH_STRICT=1 DASH_BASELINE=stata "$$py" -m pytest test/ $(PYTEST_ARGS)

test-dev:
	@echo "pytest under the development interpreter: $(PYTHON)"
	@DASH_STRICT=1 DASH_BASELINE=dev $(PYTHON) -m pytest test/ $(PYTEST_ARGS)

# WP-30 P1.33: one leg of the Python floor matrix, run by hand; make gate
# never runs it.  FLOOR_VENV is a venv directory scripts/floor_matrix.sh make
# prepared, FLOOR_BASELINE the test/conftest.py baseline it is held to.
test-floor:
	@if [ -z "$(FLOOR_VENV)" ] || [ -z "$(FLOOR_BASELINE)" ]; then \
	    echo "make test-floor: set FLOOR_VENV (prepared by scripts/floor_matrix.sh make) and FLOOR_BASELINE (e.g. py311)"; \
	    exit 2; \
	fi; \
	PYTEST_ARGS='$(PYTEST_ARGS)' sh scripts/floor_matrix.sh run "$(FLOOR_VENV)" "$(FLOOR_BASELINE)"

cert:
	@STATA_BIN='$(STATA_BIN)' PYTHON='$(PYTHON)' sh scripts/run_cert_suite.sh

gate:
	@STATA_BIN='$(STATA_BIN)' PYTHON='$(PYTHON)' sh scripts/run_release_gate.sh

release: check gate

hooks:
	git config core.hooksPath scripts/git-hooks
	@echo "git push now runs 'make check' first; 'git push --no-verify' skips it."
