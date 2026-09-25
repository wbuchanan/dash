#!/bin/sh
# scripts/stata_slot.sh <scratch-dir> <file.do>: run Stata in batch from <scratch-dir>
# holding one of three slots, so at most three sessions run at once.
set -u
dir="$1"; dofile="$2"; mkdir -p "$dir/tmp"
while :; do
  for n in 1 2 3; do
    if mkdir "/tmp/dash-stata-slot-$n.d" 2>/dev/null; then
      trap 'rmdir "/tmp/dash-stata-slot-'"$n"'.d"' EXIT
      cd "$dir" && STATATMP="$dir/tmp/" arch -arm64 /usr/local/bin/stata-mp -b do "$dofile"
      exit $?
    fi
  done
  sleep 5
done
