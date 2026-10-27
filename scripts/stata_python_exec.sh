#!/bin/sh
# Print the Python every Stata-built dashboard is rendered with, read from
# Stata itself, through the console binary in batch (never the GUI binary,
# which parks on a modal alert): c(python_exec) when a Python is set, and
# with none set, the interpreter Stata found by itself, read from inside it
# (sys.executable; WP-36 plat:PT-1, M8) -- never `python query'.  Exits 1,
# printing nothing to stdout, when Stata or its Python cannot be run.
# Stata is started by scripts/stata_batch.sh, so STATA_BIN names the console
# binary.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
dir="$(mktemp -d "${TMPDIR:-/tmp}/dash_pyexec.XXXXXX")" || exit 1
trap 'rm -rf "$dir"' EXIT
mkdir -p "$dir/tmp"
cat > "$dir/pyexec.do" <<'EOT'
local _pyx `"`c(python_exec)'"'
if `"`_pyx'"' == "" {
    python: import sys; from sfi import Macro; Macro.setLocal("_pyx", sys.executable)
}
file open fh using "pyexec.txt", write text replace
file write fh `"`_pyx'"'
file close fh
EOT
(cd "$dir" && STATATMP="$dir/tmp/" sh "$REPO/scripts/stata_batch.sh" -b do pyexec.do \
    >/dev/null 2>&1)
if [ -s "$dir/pyexec.txt" ]; then
    cat "$dir/pyexec.txt"
    echo
    exit 0
fi
echo "stata_python_exec: could not read the Python Stata runs from ${STATA_BIN:-/usr/local/bin/stata-mp}" >&2
exit 1
