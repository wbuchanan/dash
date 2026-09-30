"""Merge probes measured by scripts/extract_value_truth_additions.do into
test/fixtures/value_truth.json.

    python3 scripts/merge_value_truth.py <probe-dir> <note>

Each probe_<id>.rc holds rc, option, value and command, one per line; its
probe_<id>.log holds twoway's output, whose non-blank lines are joined by a
blank into "message" (the fixture's existing form).  A record whose id is
already in the fixture is refused, never overwritten, so a pre-existing
measurement cannot change.  The counts are recomputed and <note> is appended
to _meta.additions.
"""
import glob
import json
import os
import re
import sys

_FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                    "test", "fixtures", "value_truth.json")
_ID = re.compile(r"^[a-z0-9]+_[0-9]+$")


def read_probe(rc_path):
    """One fixture record from a probe's .rc and .log files."""
    with open(rc_path, encoding="utf-8") as fh:
        rc, option, value, command = fh.read().split("\n")[:4]
    pid = os.path.basename(rc_path)[len("probe_"):-len(".rc")]
    if not _ID.match(pid):
        raise ValueError("bad probe id %r" % pid)
    with open(rc_path[:-3] + ".log", encoding="utf-8") as fh:
        lines = [ln.strip() for ln in fh.read().splitlines()]
    return {"id": pid, "option": option, "value": value, "command": command,
            "rc": int(rc), "message": " ".join(ln for ln in lines if ln)}


def _order(rec):
    head, n = rec["id"].rsplit("_", 1)
    return (head, int(n))


def merge(fixture, records, note):
    """fixture with records appended, counts recomputed and note added."""
    have = {p["id"] for p in fixture["twoway"]}
    dup = sorted(r["id"] for r in records if r["id"] in have)
    if dup:
        raise ValueError("already measured: %s" % ", ".join(dup))
    fixture["twoway"].extend(sorted(records, key=_order))
    tw = fixture["twoway"]
    c = fixture["_meta"]["counts"]
    c["twoway"] = len(tw)
    c["twoway_rc0"] = sum(1 for p in tw if p["rc"] == 0)
    c["twoway_rejected"] = c["twoway"] - c["twoway_rc0"]
    fixture["_meta"].setdefault("additions", []).append(note)
    return fixture


def main(argv):
    probe_dir, note = argv[1], argv[2]
    records = [read_probe(p) for p in
               glob.glob(os.path.join(probe_dir, "probe_*.rc"))]
    with open(_FIX, encoding="utf-8") as fh:
        fixture = json.load(fh)
    merge(fixture, records, note)
    with open(_FIX, "w", encoding="utf-8") as fh:
        json.dump(fixture, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


if __name__ == "__main__":
    main(sys.argv)
