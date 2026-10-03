#!/bin/sh
# WP-27's release gate: net install dash from a copy of exactly what dash.pkg
# ships into a scratch PLUS, run every example and one page per shipped
# scheme from the installed tree, and have adoupdate compare the install with
# its source (scripts/release_gate.do); then judge the run from its logs with
# scripts/release_verdict.py.  Stata is run as CLAUDE.md rule 22 requires --
# the console binary, in batch -- with its own STATATMP, which must end in
# "/" and must not be the directory the batch log is written to.  STATA names
# the console binary and PYTHON the interpreter the verdict runs under.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
STATA="${STATA:-/usr/local/bin/stata-mp}"
PYTHON="${PYTHON:-python3}"
dir="$(mktemp -d "${TMPDIR:-/tmp}/dash_release.XXXXXX")" || exit 1
mkdir -p "$dir/tmp" "$dir/src" "$dir/work"

# The source: dash.pkg's f lines, stata.toc and dash.pkg, nothing else.
shipped="$(sed -n 's/^f  *\([^ ]*\) *$/\1/p' "$REPO/dash.pkg")"
for f in $shipped; do
    mkdir -p "$dir/src/$(dirname "$f")"
    cp "$REPO/$f" "$dir/src/$f" || { echo "release gate: $f is missing"; exit 1; }
done
cp "$REPO/dash.pkg" "$REPO/stata.toc" "$dir/src/"

# The newest change to a shipped file: today when one is uncommitted.
cd "$REPO" || exit 1
if [ -n "$(git status --porcelain -- dash.pkg stata.toc $shipped)" ]; then
    newest="$(date +%Y%m%d)"
else
    newest="$(git log -1 --format=%cd --date=format:%Y%m%d -- dash.pkg stata.toc $shipped)"
fi

echo "release gate: running in $dir"
(cd "$dir" && STATATMP="$dir/tmp/" arch -arm64 "$STATA" -b do \
    "$REPO/scripts/release_gate.do" "$dir/src" "$dir/work" "$REPO/examples" \
    >/dev/null 2>&1)
# Stata's batch mode names its log after the command line's last word, not
# the do-file, so the log is the one .log the run wrote in $dir.
log="$(ls -t "$dir"/*.log 2>/dev/null | head -1)"
# WP-29 P0.19: the venv-linked sessions, from $dir/work so the second links by a relative path.
for phase in venvmake venvuse; do
    (cd "$dir/work" && PIP_NO_INDEX=1 STATATMP="$dir/tmp/" arch -arm64 "$STATA" -b do \
        "$REPO/scripts/release_gate_venv.do" "$dir/work" "$dir/work/plus/" plus "$phase" >/dev/null 2>&1)
    # Batch mode names the log after the command line's text past its last
    # /, here " plus <phase>.log": moved to the name the verdict reads.
    for f in "$dir/work/"*" $phase.log"; do
        [ -f "$f" ] && mv -f "$f" "$dir/work/$phase.log"
    done
done
"$PYTHON" "$REPO/scripts/release_verdict.py" "${log:-$dir/release_gate.log}" \
    "$REPO" "$newest" "$dir/work/venvmake.log" "$dir/work/venvuse.log"
rc=$?
echo "release gate log: ${log:-none}"
exit $rc
