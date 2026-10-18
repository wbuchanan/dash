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
# The certification suite's Stata sessions, side by side (1 to 4; WP-30).
DASH_CERT_SESSIONS ?= 3

ifeq ($(origin STATA),command line)
$(error STATA was renamed STATA_BIN (WP-30); run make $(MAKECMDGOALS) STATA_BIN=$(STATA))
endif

.PHONY: help check test test-dev test-batch test-release test-all test-floor cert gate release hooks lint

help:
	@echo "make check     make test, make test-dev and make cert, in that order"
	@echo "make test      pytest under Stata's Python, strict"
	@echo "make test-dev  pytest under the development interpreter ($(PYTHON)), strict"
	@echo "make test-release  the release tier, the tests marked release, which make test and make test-dev leave out"
	@echo "make test-batch  the batch tier (test_mode_parity.py), which make test and make test-dev leave out"
	@echo "make test-all  the batch-end suite: pytest with the batch tier, then the certification scripts, never more than 8 workers at once (PYTEST_WORKERS, default 8; DASH_CERT_SESSIONS, default 3)"
	@echo "make test-floor  one floor-matrix leg, run by hand (not part of make gate): FLOOR_VENV=<dir> FLOOR_BASELINE=<name>"
	@echo "make cert      the certification suite, through the console binary, as DASH_CERT_SESSIONS (default 3, 1 to 4) sessions side by side; DASH_CERT_REMEASURE=1 asks twoway again (release)"
	@echo "make gate      net install, then every example and scheme from the install"
	@echo "make release   make check, then make test-release, then make gate"
	@echo "make hooks     have 'git push' run 'make check' first"
	@echo "make lint      ruff over dash_render.py, dash_setup_lib.py, test/ and scripts/ with ruff.toml (RUFF=<command> names ruff; it is not a runtime dependency)"
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

# DEV_STRICT and DEV_BASELINE (WP-31 I6): the CI workflow runs on a Linux
# runner with no Stata, node or Chrome, so tests that need them skip, and
# its Python 3.11 is the py311 baseline; it sets DEV_STRICT=0
# DEV_BASELINE=py311.  On the certified machine both keep their defaults.
DEV_STRICT   ?= 1
DEV_BASELINE ?= dev
test-dev:
	@echo "pytest under the development interpreter: $(PYTHON)"
	@DASH_STRICT=$(DEV_STRICT) DASH_BASELINE=$(DEV_BASELINE) $(PYTHON) -m pytest test/ $(PYTEST_ARGS)

# The release tier (WP-30 test performance D): the tests marked release --
# headless Chrome, nested pytest runs, the scipy/statsmodels-free subprocess
# sweeps, datasets over the size threshold -- which a run of the whole suite
# leaves out (test/conftest.py).  make release runs it after make check.
test-release:
	@echo "pytest's release tier under the development interpreter: $(PYTHON)"
	@DASH_STRICT=1 DASH_BASELINE=dev DASH_TEST_TIER=release $(PYTHON) -m pytest test/ -m release $(PYTEST_ARGS)

# The batch tier: test_mode_parity.py, which a run of the whole suite
# leaves out (test/conftest.py).  make test-all and make release run it.
test-batch:
	@echo "pytest's batch tier under the development interpreter: $(PYTHON)"
	@DASH_STRICT=1 DASH_BASELINE=dev DASH_TEST_TIER=batch $(PYTHON) -m pytest test/ -m batch $(PYTEST_ARGS)

# The batch-end suite in one command: pytest under the development
# interpreter with the batch tier, then the certification scripts, never
# on more than eight workers at once (scripts/run_all_tests.sh refuses
# more).  Run at the end of every batch of work and before a release.
test-all:
	@PYTHON='$(PYTHON)' STATA_BIN='$(STATA_BIN)' sh scripts/run_all_tests.sh

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
	@STATA_BIN='$(STATA_BIN)' PYTHON='$(PYTHON)' DASH_CERT_SESSIONS='$(DASH_CERT_SESSIONS)' sh scripts/run_cert_suite.sh

gate:
	@STATA_BIN='$(STATA_BIN)' PYTHON='$(PYTHON)' sh scripts/run_release_gate.sh

release: check test-batch test-release gate

hooks:
	git config core.hooksPath scripts/git-hooks
	@echo "git push now runs 'make check' first; 'git push --no-verify' skips it."

# WP-31 I6: ruff with the committed ruff.toml.  ruff is a development tool,
# not a dependency: RUFF names it, else $(PYTHON) -m ruff, else ruff on PATH.
LINT_PATHS = dash_render.py dash_setup_lib.py test scripts
lint:
	@r='$(RUFF)'; \
	if [ -z "$$r" ]; then \
	    if $(PYTHON) -m ruff --version >/dev/null 2>&1; then r='$(PYTHON) -m ruff'; \
	    elif command -v ruff >/dev/null 2>&1; then r=ruff; fi; \
	fi; \
	if [ -z "$$r" ]; then \
	    echo "make lint: ruff is not installed; install it with '$(PYTHON) -m pip install ruff' (a development tool, not a dependency of dash), or name it with RUFF=<command>"; \
	    exit 2; \
	fi; \
	$$r check $(LINT_PATHS) --config ruff.toml
