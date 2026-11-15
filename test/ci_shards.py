"""Split the suite's test files into shards for CI (DASH_SHARD=k/N).

GitHub's runner for this repository has 2 CPUs and about 8 GB: the whole
default tier on one runner ran past its hour (14nov2026), so the CI
workflow runs it as N jobs, job k with DASH_SHARD=k/N, and each job
collects only shard k's test files (conftest.pytest_ignore_collect).

The shards are balanced longest first, as scripts/cert_shards.py balances
the certification scripts: the files, from the longest, each go to the
least loaded shard (the lowest numbered of equals).  A file's weight is its
test-seconds in the table beside this file (ci_shard_seconds.json); a file
the table does not list weighs the table's median.  The table is written
from a suite timing report (DASH_SUITE_TIMING, which make test-all writes
as pytest_timing.json) by running this file with the report's path.
"""
import json
import os
import statistics
import sys
from collections import namedtuple

TABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "ci_shard_seconds.json")

#: Shard *k* of *n*: its test files (paths from the repository root, as
#: "test/test_x.py") and how many files the run split.
Shard = namedtuple("Shard", "k n files of")


def parse(value):
    """``"k/N"`` as ``(k, N)``, 1 <= k <= N; ValueError otherwise."""
    parts = value.strip().split("/")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        raise ValueError("not k/N")
    k, n = int(parts[0]), int(parts[1])
    if not 1 <= k <= n:
        raise ValueError("k must be from 1 to N")
    return k, n


def load_seconds(path=TABLE):
    """The table's test-seconds by file; {} when there is no table."""
    try:
        with open(path, encoding="utf-8") as fh:
            return dict(json.load(fh)["seconds"])
    except OSError:
        return {}


def weight(name, seconds):
    """*name*'s seconds in *seconds*, else their median (1 s if empty)."""
    if name in seconds:
        return seconds[name]
    return statistics.median(seconds.values()) if seconds else 1.0


def assign(files, seconds, n):
    """Each of *files* mapped to its shard, 1 to *n*: longest first onto
    the least loaded shard, the lowest numbered of equals."""
    loads = [0.0] * n
    got = {}
    for name in sorted(files, key=lambda f: (-weight(f, seconds), f)):
        k = loads.index(min(loads))
        loads[k] += weight(name, seconds)
        got[name] = k + 1
    return got


def seconds_from_report(report):
    """A timing report's test-seconds by file, to a tenth of a second."""
    return {f["file"]: round(f["seconds"], 1) for f in report["files"]}


def main(argv):
    """``ci_shards.py <pytest_timing.json> [table]``: write the table."""
    if not argv or len(argv) > 2:
        sys.stderr.write("usage: ci_shards.py <pytest_timing.json> [table]\n")
        return 2
    with open(argv[0], encoding="utf-8") as fh:
        report = json.load(fh)
    table = {"note": "test-seconds by file, from a DASH_SUITE_TIMING report "
                     "(%s); ci_shards.py writes it" % os.path.basename(argv[0]),
             "seconds": seconds_from_report(report)}
    with open(argv[1] if len(argv) > 1 else TABLE, "w",
              encoding="utf-8") as fh:
        json.dump(table, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
