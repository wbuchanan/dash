#!/usr/bin/env bash
# Function coverage of dash_render.py under the whole pytest suite (WP-24,
# AC-24.3: every function has a behavioural test).  Not run by default:
# it is a full suite run, so it takes as long as one (a few minutes on
# twelve workers; per-test attribution adds a little).  Standard library
# only -- coverage.py is not needed.
#
#   scripts/fncov/run_fncov.sh [OUTDIR] [-- EXTRA PYTEST ARGS]
#
# OUTDIR defaults to $TMPDIR/dash-fncov.  Any fncov-*.jsonl already in it are
# deleted first (nothing else is).  Writes OUTDIR/report.json and prints:
#
#   * per kind (module-level function, method, nested function, app template
#     function) how many there are and how many were never executed;
#   * every dash_render.py function never executed, with its line;
#   * every app template function never executed;
#   * every function the served app copies and never runs.
#
# Set in the environment, for more:
#
#   DASH_FNCOV_PER_TEST=1  tag each record with the test that ran it, so
#                          fncov_report.py --suggest-map (the most focused
#                          test per function), --check-map (entries of
#                          test/function_test_map.py whose test did not run
#                          their function) and --exclude-tests (coverage
#                          without some tests) can be answered;
#   DASH_FNCOV_CALLERS=1   also record whether anything but a test called
#                          each function; the report then lists the ones
#                          only tests call.
#
# How it measures (the files beside this one say more):
#
#   dash_fncov_recorder.py  sys.monitoring PY_START, one event per code
#                           object per process (per test, per-test), written
#                           as it happens;
#   dash_fncov_plugin.py    starts it in pytest and every xdist worker
#                           (-p dash_fncov_plugin) and puts site/ on the
#                           PYTHONPATH children inherit;
#   site/usercustomize.py   starts it in every Python subprocess a test
#                           launches (python app.py, bokeh serve, ...);
#   fncov_report.py         merges the files and maps each function of a
#                           generated app back to dash_render.py.
#
# Two companions, not run here:
#
#   fncov_reach.py          the static half: which functions no code that
#                           runs in either mode can reach (dead code);
#   fncov_mutate.py         the other question -- would a test notice?  It
#                           skips each function's body in a scratch copy and
#                           runs the tests that execute it (report.json of a
#                           per-test run), most focused first.
#
# test/test_function_test_map.py keeps test/function_test_map.py honest on
# every ordinary run: it fails when dash_render.py gains a function the map
# does not name, when the map names a test that does not exist, or when a
# function the map calls dead or test-only becomes reachable.
#
# CLAUDE.md rule 23 applies: never start this while another full run is
# executing.
set -u
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../.." && pwd)"
out="${1:-${TMPDIR:-/tmp}/dash-fncov}"
[ $# -gt 0 ] && shift
[ "${1:-}" = "--" ] && shift
mkdir -p "$out"
rm -f "$out"/fncov-*.jsonl
cd "$root" || exit 2
status=0
DASH_FNCOV_DIR="$out" \
PYTHONPATH="$here/site:$here${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -m pytest test/ -q -p no:cacheprovider -p dash_fncov_plugin \
  -n auto --dist loadgroup "$@" || status=$?
python3 "$here/fncov_report.py" "$out" --json "$out/report.json" || status=$?
exit "$status"
