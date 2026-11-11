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
# The certification suite's Stata sessions, side by side (1 to 8; WP-30).
DASH_CERT_SESSIONS ?= 3

ifeq ($(origin STATA),command line)
$(error STATA was renamed STATA_BIN (WP-30); run make $(MAKECMDGOALS) STATA_BIN=$(STATA))
endif

.PHONY: help check test test-dev test-batch test-release test-all test-floor cert cert-release cert-all gate release hooks truth truth-check lint corpus gallery

help:
	@echo "make check     make test, make test-dev and make cert, in that order"
	@echo "make test      pytest under Stata's Python, strict"
	@echo "make test-dev  pytest under the development interpreter ($(PYTHON)), strict"
	@echo "make test-release  the release tier, the tests marked release, which make test and make test-dev leave out"
	@echo "make test-batch  the batch tier (test_mode_parity.py), which make test and make test-dev leave out"
	@echo "make test-all  the batch-end suite: pytest with the batch tier, then the certification scripts, never more than 8 workers at once (PYTEST_WORKERS, default 8; DASH_CERT_SESSIONS, default 8)"
	@echo "make test-floor  one floor-matrix leg, run by hand (not part of make gate): FLOOR_VENV=<dir> FLOOR_BASELINE=<name>"
	@echo "make cert      the certification suite, through the console binary, as DASH_CERT_SESSIONS (default 3, 1 to 8) sessions side by side; DASH_CERT_REMEASURE=1 asks twoway again (release)"
	@echo "make cert-release  the certification suite's release tier alone: the closed work packages' truth scripts (test_wp29/30/31_truth), which make cert and make test-all leave out"
	@echo "make cert-all  every certification script, both tiers (a work package's closeout)"
	@echo "make gate      net install, then every example and scheme from the install, then the certification scripts (GATE_CERT_TIER, default all; make release runs the release tier, its make check having run the default)"
	@echo "make release   make check, then make test-release, then make gate"
	@echo "make hooks     have 'git push' run 'make check' first"
	@echo "make lint      ruff over dash_render.py, dash_setup_lib.py, test/ and scripts/ with ruff.toml (RUFF=<command> names ruff; it is not a runtime dependency)"
	@echo "make truth     regenerate every truth fixture: each scripts/extract_*.do through one Stata slot, one at a time, then the Python generators (hours; never part of make test)"
	@echo "make truth-check  the fixture guard: every fixture names its generator, carries complete _meta and holds no absolute path"
	@echo "make corpus    compare every twoway example (help files, g.pdf, examples/, the audit's probes; one per combination of plot types and options) with dash into CORPUS_DIR (default $$TMPDIR/dash_corpus; hours, Stata and Chrome; never part of make test)"
	@echo "make gallery   write docs/gallery/ (SVG pairs, corpus.json, one dash page per plot type and an index page) and README.md's gallery block from CORPUS_DIR (run at WP-50's closeout)"
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

# The release tier (22oct2026): the closed work packages' truth scripts
# (the runner's _cert_release line), which make cert and make test-all
# leave out.  make cert-release runs them alone, make cert-all every
# certification script -- the run of a work package's closeout.
cert-release:
	@STATA_BIN='$(STATA_BIN)' PYTHON='$(PYTHON)' DASH_CERT_SESSIONS='$(DASH_CERT_SESSIONS)' DASH_CERT_TIER=release sh scripts/run_cert_suite.sh

cert-all:
	@STATA_BIN='$(STATA_BIN)' PYTHON='$(PYTHON)' DASH_CERT_SESSIONS='$(DASH_CERT_SESSIONS)' DASH_CERT_TIER=all sh scripts/run_cert_suite.sh

# The gate runs the certification scripts of GATE_CERT_TIER after the
# install: every one when run alone; under make release, whose make check
# ran the default tier, the release tier, so that each runs once.
GATE_CERT_TIER ?= all
gate:
	@STATA_BIN='$(STATA_BIN)' PYTHON='$(PYTHON)' DASH_CERT_SESSIONS='$(DASH_CERT_SESSIONS)' DASH_CERT_TIER='$(GATE_CERT_TIER)' sh scripts/run_release_gate.sh

release: GATE_CERT_TIER = release
release: check test-batch test-release gate

hooks:
	git config core.hooksPath scripts/git-hooks
	@echo "git push now runs 'make check' first; 'git push --no-verify' skips it."

# WP-31 K3: every truth fixture from its committed generator.  Each
# scripts/extract_*.do runs through scripts/stata_slot.sh, one at a time
# (concurrent Stata sessions can unlink Python from Stata's settings),
# from TRUTH_DIR with DASH_REPO naming this checkout; then the Python
# generators that need no arguments.  pip_refusals.json takes arguments
# (scripts/extract_pip_refusals.py --managed/--plain; WP-32 used
# /opt/homebrew/bin/python3.13 and /opt/anaconda3/bin/python3) and is named,
# not run.
TRUTH_DIR ?= $(or $(TMPDIR),/tmp)/dash_truth
truth:
	@mkdir -p "$(TRUTH_DIR)"; failed=0; \
	for f in scripts/extract_*.do; do \
	    echo "make truth: $$f"; \
	    DASH_REPO='$(CURDIR)' sh scripts/stata_slot.sh "$(TRUTH_DIR)" "$(CURDIR)/$$f" >/dev/null 2>&1 || failed=1; \
	    log="$(TRUTH_DIR)/$$(basename "$$f" .do).log"; \
	    if grep -q '^r([0-9]*);' "$$log" 2>/dev/null; then echo "make truth: $$f failed, see $$log"; failed=1; fi; \
	done; \
	for py in scripts/extract_scheme_truth.py scripts/extract_color_truth.py scripts/gen_utf8_cases.py; do \
	    echo "make truth: $$py"; $(PYTHON) "$$py" || failed=1; \
	done; \
	echo "make truth: run by hand: $(PYTHON) scripts/extract_pip_refusals.py --managed <python> --plain <python> --out test/fixtures/pip_refusals.json"; \
	echo "make truth: run by hand after a corpus run: $(PYTHON) scripts/corpus/calibrate.py --write <run>; $(PYTHON) scripts/corpus/ledger.py --run <run>"; \
	echo "make truth: run by hand after make corpus: $(PYTHON) scripts/corpus/summary.py --run <run> --out test/fixtures/corpus_baseline.json"; \
	git status --short -- test/fixtures; \
	exit $$failed

truth-check:
	@$(PYTHON) -m pytest test/test_fixtures_are_committed.py -q -p no:cacheprovider

# WP-33 33-08: the corpus comparison and its publication.  make corpus runs
# the five stages into CORPUS_DIR, outside the repository (make stops at a
# failing stage, which reruns alone); make gallery builds docs/gallery/ and
# README.md's gallery block from it, at WP-50's closeout only.  Neither is
# part of make test, make test-all, make check or make cert.
CORPUS_DIR ?= $(or $(TMPDIR),/tmp)/dash_corpus
GALLERY_DIR ?= $(CURDIR)/docs/gallery
corpus:
	@mkdir -p "$(CORPUS_DIR)"
	$(PYTHON) scripts/corpus/extract.py --out "$(CORPUS_DIR)"
	$(PYTHON) scripts/corpus/datasets.py --fetch "$(CORPUS_DIR)"
	$(PYTHON) scripts/corpus/twoway_run.py --run "$(CORPUS_DIR)"
	$(PYTHON) scripts/corpus/dash_run.py --run "$(CORPUS_DIR)"
	$(PYTHON) scripts/corpus/verdict.py --run "$(CORPUS_DIR)"
	$(PYTHON) scripts/corpus/summary.py --run "$(CORPUS_DIR)"
	@echo "make corpus: results in $(CORPUS_DIR)"

gallery:
	$(PYTHON) scripts/corpus/gallery.py --run "$(CORPUS_DIR)" --gallery "$(GALLERY_DIR)" --readme README.md

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
