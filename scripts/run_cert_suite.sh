#!/bin/sh
# Run the certification suite as CLAUDE.md rule 22 requires -- the console
# binary, in batch -- from a scratch directory with its own STATATMP (which
# must end in "/" and must not be the directory the batch log is written
# to), then judge the run from its log with scripts/cert_verdict.py: it
# passes only when every script test/run_all_cscripts.do registers passed
# and none skipped.  Stata's batch mode does not return the runner's exit
# status, so the log is the verdict.  STATA names the console binary and
# PYTHON the interpreter the verdict script runs under.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
STATA="${STATA:-/usr/local/bin/stata-mp}"
PYTHON="${PYTHON:-python3}"
dir="$(mktemp -d "${TMPDIR:-/tmp}/dash_cert.XXXXXX")" || exit 1
mkdir -p "$dir/tmp"
echo "certification suite: running in $dir"
(cd "$dir" && STATATMP="$dir/tmp/" arch -arm64 "$STATA" -b do \
    "$REPO/test/run_all_cscripts.do" >/dev/null 2>&1)
"$PYTHON" "$REPO/scripts/cert_verdict.py" "$dir/run_all_cscripts.log" \
    "$REPO/test/run_all_cscripts.do"
rc=$?
echo "certification log: $dir/run_all_cscripts.log"
exit $rc
