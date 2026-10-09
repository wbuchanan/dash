#!/bin/sh
# scripts/stata_batch.sh [Stata arguments]: start console Stata with the
# arguments unchanged, so Stata names its batch log as it always has
# (WP-30 P1.34).  STATA_BIN names the binary (default /usr/local/bin/stata-mp;
# it is never searched for).  STATA_ARCH is auto (default), none, arm64 or
# x86_64: auto starts the arm64 slice exactly when the machine reports
# hw.optional.arm64 = 1 and the binary holds an arm64 slice -- never from
# uname -m, which reports x86_64 under an x86_64 parent process.
# STATA_BATCH_PRINT=1 prints the command instead of running it.
set -u
bin="${STATA_BIN:-/usr/local/bin/stata-mp}"
mode="${STATA_ARCH:-auto}"
case "$mode" in
  auto|none|arm64|x86_64) ;;
  *) echo "stata_batch: STATA_ARCH must be auto, none, arm64 or x86_64" >&2; exit 2 ;;
esac
_console() {
  case "$(basename -- "$1")" in
    stata|stata-mp|stata-se|stata-be|stata-ic) return 0 ;;
  esac
  return 1
}
t="$bin"; hops=0
while [ -L "$t" ] && [ "$hops" -lt 40 ]; do
  l="$(readlink -- "$t")" || break
  case "$l" in /*) t="$l" ;; *) t="$(dirname -- "$t")/$l" ;; esac
  hops=$((hops + 1))
done
if ! _console "$bin" || ! _console "$t"; then
  printf 'stata_batch: %.200s is not a console Stata (stata, stata-mp, stata-se, stata-be or stata-ic); the GUI application waits on a modal alert in batch mode\n' "$bin" >&2
  exit 2
fi
if [ ! -f "$t" ] || [ ! -x "$t" ]; then
  printf 'stata_batch: %.200s is not an executable file\n' "$bin" >&2
  exit 2
fi
want=""
case "$mode" in
  arm64|x86_64) want="$mode" ;;
  auto)
    if [ "$(uname -s)" = Darwin ] \
       && [ "$(sysctl -n hw.optional.arm64 2>/dev/null)" = 1 ] \
       && file -L -- "$bin" 2>/dev/null | grep -Eq 'executable arm64e?$'; then
      want=arm64
    fi ;;
esac
if [ -n "$want" ]; then set -- arch "-$want" "$bin" "$@"; else set -- "$bin" "$@"; fi
if [ "${STATA_BATCH_PRINT:-}" = 1 ]; then
  out=""; for a in "$@"; do out="$out${out:+ }<$a>"; done
  printf '%s\n' "$out"
  exit 0
fi
exec "$@"
