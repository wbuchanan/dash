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
#
# DASH_CERT_SESSIONS (default 3, at most 4; WP-30 test performance, C) runs
# the suite as that many Stata sessions side by side, session k running
# shard k (DASH_CERT_SHARD=k/N; the runner's shard table keeps every script
# that serves on a fixed port in one shard), each in its own folder with its
# own STATATMP; the verdict then judges their logs together.  1 runs it in
# one session, as before.  The sessions are linked to the Python Stata
# reports before they start (DASH_PYTHON_EXEC, unless it is set already),
# so a settings file rewritten by a concurrent session cannot unlink them.
# DASH_CERT_ONLY="test_a test_b" runs, and judges, only those scripts.
# DASH_CERT_TIER (22oct2026; default, release or all) runs, and judges, one
# tier: default (unset) every script but the release tier's -- the closed
# work packages' truth scripts, the runner's _cert_release line -- release
# those alone, all every script (make cert-release, make cert-all; the
# release gate and a work package's closeout).
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
n="${DASH_CERT_SESSIONS:-3}"
case "$n" in
  1|2|3|4) ;;
  *) echo "certification suite: DASH_CERT_SESSIONS must be 1, 2, 3 or 4" >&2
     exit 2 ;;
esac
only="${DASH_CERT_ONLY:-}"
case "$only" in
  *[!A-Za-z0-9_.\ ]*)
    echo "certification suite: DASH_CERT_ONLY holds script names only (letters, digits, _ and .)" >&2
    exit 2 ;;
esac
tier="${DASH_CERT_TIER:-default}"
case "$tier" in
  default|release|all) ;;
  *) echo "certification suite: DASH_CERT_TIER must be default, release or all" >&2
     exit 2 ;;
esac
dir="$(mktemp -d "${TMPDIR:-/tmp}/dash_cert.XXXXXX")" || exit 1
echo "certification suite: running in $dir"
echo "certification suite: testing $REPO"
echo "certification suite: the $tier tier"
# The logs to judge, as the positional parameters (a path may hold a blank).
set --
if [ "$n" = 1 ]; then
  mkdir -p "$dir/tmp"
  (cd "$dir" && DASH_REPO="$REPO" DASH_CERT_TIER="$tier" STATATMP="$dir/tmp/" sh "$REPO/scripts/stata_batch.sh" -b do \
      "$REPO/test/run_all_cscripts.do" >/dev/null 2>&1)
  set -- "$dir/run_all_cscripts.log"
else
  pyx="${DASH_PYTHON_EXEC:-}"
  if [ -z "$pyx" ]; then
    pyx="$(sh "$REPO/scripts/stata_python_exec.sh" 2>/dev/null)" || pyx=""
  fi
  echo "certification suite: $n sessions side by side"
  k=1
  while [ "$k" -le "$n" ]; do
    mkdir -p "$dir/s$k/tmp"
    (cd "$dir/s$k" && DASH_REPO="$REPO" DASH_CERT_SHARD="$k/$n" \
        DASH_CERT_TIER="$tier" \
        DASH_PYTHON_EXEC="$pyx" STATATMP="$dir/s$k/tmp/" \
        sh "$REPO/scripts/stata_batch.sh" -b do \
        "$REPO/test/run_all_cscripts.do" >/dev/null 2>&1) &
    set -- "$@" "$dir/s$k/run_all_cscripts.log"
    k=$((k + 1))
  done
  wait
fi
if [ -n "$only" ]; then
  "$PYTHON" "$REPO/scripts/cert_verdict.py" --only "$only" --tier "$tier" "$@" \
      "$REPO/test/run_all_cscripts.do"
else
  "$PYTHON" "$REPO/scripts/cert_verdict.py" --tier "$tier" "$@" \
      "$REPO/test/run_all_cscripts.do"
fi
rc=$?
for l in "$@"; do
  echo "certification log: $l"
done
exit $rc
