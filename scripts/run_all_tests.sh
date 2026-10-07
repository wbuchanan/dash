#!/bin/sh
# Run the whole default test suite -- pytest and the certification scripts
# -- side by side, with at most DASH_MAX_WORKERS (8) workers in all:
# PYTEST_WORKERS pytest workers (default 6) and DASH_CERT_SESSIONS Stata
# sessions (default 2).  The two halves start together; the run ends when
# both have, and fails if either failed.  Their logs are kept in a fresh
# folder under TMPDIR, named at the end.  DRY_RUN=1 prints the two commands
# and runs nothing.  The release tier (make test-release) is not part of it.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
max="${DASH_MAX_WORKERS:-8}"
pw="${PYTEST_WORKERS:-6}"
cs="${DASH_CERT_SESSIONS:-2}"
for v in "$max" "$pw" "$cs"; do
    case "$v" in
        ''|*[!0-9]*) echo "run_all_tests: worker counts must be whole numbers"; exit 2 ;;
    esac
done
if [ "$pw" -lt 1 ] || [ "$cs" -lt 1 ] || [ "$cs" -gt 4 ]; then
    echo "run_all_tests: PYTEST_WORKERS must be at least 1 and DASH_CERT_SESSIONS 1 to 4"
    exit 2
fi
if [ $((pw + cs)) -gt "$max" ]; then
    echo "run_all_tests: $pw pytest workers and $cs Stata sessions exceed $max workers"
    exit 2
fi
pytest_cmd="DASH_STRICT=1 DASH_BASELINE=dev FULL_SUITE_RERUN=1 $PYTHON -m pytest test/ -q -p no:cacheprovider -n $pw"
cert_cmd="DASH_CERT_SESSIONS=$cs sh scripts/run_cert_suite.sh"
if [ "${DRY_RUN:-}" = 1 ]; then
    echo "pytest: $pytest_cmd"
    echo "cert:   $cert_cmd"
    exit 0
fi
out="$(mktemp -d "${TMPDIR:-/tmp}/dash_all_tests.XXXXXX")" || exit 1
cd "$REPO" || exit 2
start=$(date +%s)
( t0=$(date +%s)
  DASH_STRICT=1 DASH_BASELINE=dev FULL_SUITE_RERUN=1 "$PYTHON" -m pytest test/ -q -p no:cacheprovider -n "$pw" > "$out/pytest.log" 2>&1
  echo "rc=$? wall=$(( $(date +%s) - t0 ))" > "$out/pytest.rc" ) &
pp=$!
( t0=$(date +%s)
  DASH_CERT_SESSIONS="$cs" PYTHON="$PYTHON" sh scripts/run_cert_suite.sh > "$out/cert.log" 2>&1
  echo "rc=$? wall=$(( $(date +%s) - t0 ))" > "$out/cert.rc" ) &
cp=$!
wait "$pp"
wait "$cp"
total=$(( $(date +%s) - start ))
prc=$(sed -n 's/^rc=\([0-9]*\).*/\1/p' "$out/pytest.rc")
crc=$(sed -n 's/^rc=\([0-9]*\).*/\1/p' "$out/cert.rc")
echo "pytest ($pw workers): $(tail -1 "$out/pytest.log" | tr -d '=') [$(cat "$out/pytest.rc")]"
echo "cert ($cs sessions): $(grep -E '^verdict' "$out/cert.log" | tail -1) [$(cat "$out/cert.rc")]"
echo "whole suite: ${total} s wall on $((pw + cs)) workers; logs in $out"
[ "$prc" = 0 ] && [ "$crc" = 0 ]
