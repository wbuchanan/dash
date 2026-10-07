#!/bin/sh
# Run the whole default test suite -- pytest, then the certification
# scripts -- never using more than DASH_MAX_WORKERS (8) workers at once:
# PYTEST_WORKERS pytest workers (default 8), then DASH_CERT_SESSIONS Stata
# sessions (default 3).  They run one after the other: run side by side
# (measured 07oct2026, 6 + 2 workers) pytest's serve tests and the
# certification scripts that serve on fixed ports fought over ports and
# CPU, and seven serve tests failed.  The run fails if either half failed.
# Their logs are kept in a fresh folder under TMPDIR, named at the end.
# DRY_RUN=1 prints the two commands and runs nothing.  The release tier
# (make test-release) is not part of it.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
max="${DASH_MAX_WORKERS:-8}"
pw="${PYTEST_WORKERS:-8}"
cs="${DASH_CERT_SESSIONS:-3}"
for v in "$max" "$pw" "$cs"; do
    case "$v" in
        ''|*[!0-9]*) echo "run_all_tests: worker counts must be whole numbers"; exit 2 ;;
    esac
done
if [ "$pw" -lt 1 ] || [ "$cs" -lt 1 ] || [ "$cs" -gt 4 ]; then
    echo "run_all_tests: PYTEST_WORKERS must be at least 1 and DASH_CERT_SESSIONS 1 to 4"
    exit 2
fi
if [ "$pw" -gt "$max" ] || [ "$cs" -gt "$max" ]; then
    echo "run_all_tests: $pw pytest workers or $cs Stata sessions exceed $max workers"
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
t0=$(date +%s)
DASH_STRICT=1 DASH_BASELINE=dev FULL_SUITE_RERUN=1 "$PYTHON" -m pytest test/ -q -p no:cacheprovider -n "$pw" > "$out/pytest.log" 2>&1
echo "rc=$? wall=$(( $(date +%s) - t0 ))" > "$out/pytest.rc"
t0=$(date +%s)
DASH_CERT_SESSIONS="$cs" PYTHON="$PYTHON" sh scripts/run_cert_suite.sh > "$out/cert.log" 2>&1
echo "rc=$? wall=$(( $(date +%s) - t0 ))" > "$out/cert.rc"
total=$(( $(date +%s) - start ))
prc=$(sed -n 's/^rc=\([0-9]*\).*/\1/p' "$out/pytest.rc")
crc=$(sed -n 's/^rc=\([0-9]*\).*/\1/p' "$out/cert.rc")
echo "pytest ($pw workers): $(tail -1 "$out/pytest.log" | tr -d '=') [$(cat "$out/pytest.rc")]"
echo "cert ($cs sessions): $(grep -E '^verdict' "$out/cert.log" | tail -1) [$(cat "$out/cert.rc")]"
echo "whole suite: ${total} s wall, at most $max workers at once; logs in $out"
[ "$prc" = 0 ] && [ "$crc" = 0 ]
