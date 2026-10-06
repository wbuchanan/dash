#!/bin/sh
# Run the certification suite through the console binary, in batch (never
# the GUI application, which waits on a modal alert), from a scratch
# directory with its own STATATMP (which must end in "/" and must not be the
# directory the batch log is written to), then judge the run from its log
# with scripts/cert_verdict.py: it passes only when every script
# test/run_all_cscripts.do registers passed and none skipped.  Stata's batch
# mode does not return the runner's exit status, so the log is the verdict.
# The tree under test is this checkout, whichever it is: it is handed to
# the runner as DASH_REPO.  Stata is started by scripts/stata_batch.sh, so
# STATA_BIN names the console binary; PYTHON names the interpreter the
# verdict script runs under.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
cr="$(printf '\r')"
nl='
'
case "$REPO" in
  *[\"\$\'\`]*|*"$nl"*|*"$cr"*)
    echo "certification suite: this checkout's path holds a quote, dollar sign, backtick or line break, which Stata cannot be handed" >&2
    exit 2 ;;
esac
dir="$(mktemp -d "${TMPDIR:-/tmp}/dash_cert.XXXXXX")" || exit 1
mkdir -p "$dir/tmp"
echo "certification suite: running in $dir"
echo "certification suite: testing $REPO"
(cd "$dir" && DASH_REPO="$REPO" STATATMP="$dir/tmp/" sh "$REPO/scripts/stata_batch.sh" -b do \
    "$REPO/test/run_all_cscripts.do" >/dev/null 2>&1)
"$PYTHON" "$REPO/scripts/cert_verdict.py" "$dir/run_all_cscripts.log" \
    "$REPO/test/run_all_cscripts.do"
rc=$?
echo "certification log: $dir/run_all_cscripts.log"
exit $rc
