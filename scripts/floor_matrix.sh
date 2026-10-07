#!/bin/sh
# scripts/floor_matrix.sh -- one leg of the Python floor matrix (WP-30 P1.33).
#
# Usage:
#   sh scripts/floor_matrix.sh make PYTHON VENVDIR stata|dev|fresh
#   sh scripts/floor_matrix.sh run VENVDIR BASELINE
#
# make: creates VENVDIR/gatevenv from PYTHON (an absolute path) and installs
#   into it from wheels only (--only-binary=:all:, pip's own configuration
#   ignored, its cache in VENVDIR/pip-cache): the stata or dev pins of
#   test/requirements-<set>.txt, or for "fresh" what dash_setup installs,
#   resolved now.  It then prints one "FLOOR made" line: the stack and the
#   test/conftest.py baseline it matches.
# run: from the repository root, DASH_STRICT=1 DASH_BASELINE=BASELINE
#   <VENVDIR/gatevenv/bin/python> -m pytest test/ $PYTEST_ARGS; its exit
#   status is pytest's.  node must be on PATH, or DASH_NODE set.
# FLOOR_DRY_RUN=1 prints each command as "FLOOR would run: ..." and runs none.
#
# Downloads go only into VENVDIR, which must be a scratch directory (M10):
# nothing is installed into the interpreter PYTHON names or anywhere else.
#
# Re-measuring the floor by hand (ratification item 25, "Manual only"; this
# procedure is not part of make gate, which never re-tests the floor):
#   1. When: before lowering or raising _dash_pymin in dash_setup.ado, or
#      changing a test/requirements-*.txt pin or a dash_setup package minimum.
#   2. Per candidate Python (an interpreter Stata can link; venvs in scratch
#      only): sh scripts/floor_matrix.sh make <python> <dir> stata|dev|fresh
#   3. Per venv: FLOOR_VENV=<dir> FLOOR_BASELINE=<name> make test-floor,
#      expecting 0 failed and 0 skipped.
#   4. The Stata leg: PIP_NO_INDEX=1 DASH_REPO=<repo> DASH_FLOOR_WORK=<dir>
#      scripts/stata_slot.sh <dir> <repo>/scripts/floor_stata_leg.do, then the
#      six GATE lines of <dir>/floor_stata_leg.log:
#        venv-link rc=0
#        venv-python rc=0 ver=<x.y.z>
#        venv-setup2 rc=0 linked=1
#        venv-saved rc=0 html=1
#        venv-served rc=0 health=1
#        venv-done
#   5. One certification run with
#      DASH_PYTHON_EXEC=<dir>/gatevenv/bin/python make cert
#   6. The floor is the lowest Python that passes every leg; _BASELINES in
#      test/conftest.py keeps an entry only for a passing stack, and
#      test/test_version_floor.py pins _dash_pymin to the lowest.
set -eu
REPO="$(cd "$(dirname "$0")/.." && pwd)"

usage() {
    echo "usage: sh scripts/floor_matrix.sh make PYTHON VENVDIR stata|dev|fresh" >&2
    echo "       sh scripts/floor_matrix.sh run VENVDIR BASELINE" >&2
    exit 2
}

die() {
    echo "floor_matrix.sh: $*" >&2
    exit 2
}

# Run "$@", or print it under FLOOR_DRY_RUN=1.
run_cmd() {
    if [ "${FLOOR_DRY_RUN:-}" = 1 ]; then
        printf 'FLOOR would run:'
        for a in "$@"; do
            printf ' %s' "$a"
        done
        printf '\n'
    else
        "$@"
    fi
}

absolute() {
    case "$2" in
        /*) ;;
        *) die "$1 must be an absolute path: $2" ;;
    esac
}

# The FLOOR made line, printed by the venv's Python from test/.
MADE='import importlib.metadata as m, platform, conftest as C; a = C._running_env(); n = C._baseline_name(a); d = C._env_drift(a, C._BASELINES[n]); v = lambda p: m.version(p); print("FLOOR made python=%s bokeh=%s numpy=%s pandas=%s scipy=%s baseline=%s drift=%s" % (platform.python_version(), v("bokeh"), v("numpy"), v("pandas"), v("scipy"), n, ",".join("%s:%s/%s" % (k, w, g) for k, (w, g) in sorted(d.items())) or "none"))'

make_venv() {
    [ $# -eq 3 ] || usage
    py="$1"; dir="$2"; set_="$3"
    absolute PYTHON "$py"
    if [ ! -f "$py" ] || [ ! -x "$py" ]; then
        die "no executable at $py"
    fi
    absolute VENVDIR "$dir"
    case "$set_" in
        stata|dev|fresh) ;;
        *) die "the set must be stata, dev or fresh, not $set_" ;;
    esac
    venv="$dir/gatevenv"
    if [ -e "$venv" ] && [ ! -f "$venv/pyvenv.cfg" ]; then
        die "$venv is not a virtual environment (no pyvenv.cfg); nothing was written"
    fi
    vpy="$venv/bin/python"
    PIP_CONFIG_FILE=/dev/null
    PIP_DISABLE_PIP_VERSION_CHECK=1
    PIP_CACHE_DIR="$dir/pip-cache"
    export PIP_CONFIG_FILE PIP_DISABLE_PIP_VERSION_CHECK PIP_CACHE_DIR
    if [ ! -e "$venv" ]; then
        run_cmd "$py" -m venv "$venv"
    fi
    if [ "$set_" = fresh ]; then
        run_cmd "$vpy" -m pip install --require-virtualenv --only-binary=:all: \
            packaging "bokeh>=3.8,<3.10" "numpy>=2.3" "pandas>=2.3" scipy \
            pytest pytest-xdist
    else
        run_cmd "$vpy" -m pip install --require-virtualenv --only-binary=:all: \
            -r "$REPO/test/requirements-$set_.txt"
    fi
    cd "$REPO/test"
    run_cmd "$vpy" -c "$MADE"
}

run_leg() {
    [ $# -eq 2 ] || usage
    dir="$1"; base="$2"
    case "$base" in
        stata|dev|py3[0-9][0-9]|py3[0-9][0-9]-dev) ;;
        *) die "the baseline must be stata, dev, py3NN or py3NN-dev, not $base" ;;
    esac
    absolute VENVDIR "$dir"
    vpy="$dir/gatevenv/bin/python"
    if [ ! -f "$vpy" ] || [ ! -x "$vpy" ]; then
        die "no venv python at $vpy (gatevenv/bin/python); prepare it with scripts/floor_matrix.sh make"
    fi
    if [ -z "${DASH_NODE:-}" ] && ! command -v node >/dev/null 2>&1; then
        die "node is not on PATH; set DASH_NODE to its path (a skip is red under DASH_STRICT=1)"
    fi
    DASH_STRICT=1
    DASH_BASELINE="$base"
    export DASH_STRICT DASH_BASELINE
    cd "$REPO"
    if [ "${FLOOR_DRY_RUN:-}" = 1 ]; then
        ver="(dry run)"
    else
        ver="$("$vpy" -c 'import platform; print(platform.python_version())')"
    fi
    echo "FLOOR run python=$ver baseline=$base"
    # PYTEST_ARGS is a word list by design; nothing in it is globbed.
    set -f
    # shellcheck disable=SC2086
    run_cmd env DASH_STRICT=1 "DASH_BASELINE=$base" "$vpy" -m pytest test/ \
        ${PYTEST_ARGS:--q -p no:cacheprovider}
}

[ $# -ge 1 ] || usage
cmd="$1"
shift
case "$cmd" in
    make) make_venv "$@" ;;
    run) run_leg "$@" ;;
    *) usage ;;
esac
