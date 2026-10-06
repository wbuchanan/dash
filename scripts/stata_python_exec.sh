#!/bin/sh
# Print Stata's c(python_exec) -- the Python every Stata-built dashboard is
# rendered with -- read from Stata itself, through the console binary in
# batch (never the GUI binary, which parks on a modal alert).  Exits 1,
# printing nothing to stdout, when Stata cannot be run or has no Python set.
# Stata is started by scripts/stata_batch.sh, so STATA_BIN names the console
# binary.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
dir="$(mktemp -d "${TMPDIR:-/tmp}/dash_pyexec.XXXXXX")" || exit 1
trap 'rm -rf "$dir"' EXIT
mkdir -p "$dir/tmp"
cat > "$dir/pyexec.do" <<'EOT'
file open fh using "pyexec.txt", write text replace
file write fh "`c(python_exec)'"
file close fh
EOT
(cd "$dir" && STATATMP="$dir/tmp/" sh "$REPO/scripts/stata_batch.sh" -b do pyexec.do \
    >/dev/null 2>&1)
if [ -s "$dir/pyexec.txt" ]; then
    cat "$dir/pyexec.txt"
    echo
    exit 0
fi
echo "stata_python_exec: could not read c(python_exec) from ${STATA_BIN:-/usr/local/bin/stata-mp}" >&2
exit 1
