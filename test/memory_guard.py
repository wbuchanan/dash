"""Keep a pytest run from exhausting the machine's memory.

On 01nov2026 a full run's eight workers held about 22 GB beside the
maintainer's other work and macOS ran out of memory and restarted.  Two
guards, both wired in conftest.py:

- trim_worker(): after each test module, a worker that has grown past
  WORKER_CAP_BYTES drops every test module's build caches (module-level
  dicts whose names hold CACHE, and functools caches) and collects.
- start_watchdog(): the controlling process reads the machine's available
  memory every few seconds; below the floor it stops the workers and the
  run, saying why, before the system has to.

Both read the machine: macOS's vm_stat and sysctl, or Linux's
/proc/meminfo (GitHub's runner has no vm_stat, so the guard read nothing
and never acted while eight workers exhausted its 8 GB, 14nov2026).  The
floor is FLOOR_BYTES or FLOOR_SHARE of the machine's memory, whichever is
less, and the cap is WORKER_CAP_BYTES or each worker's part of
WORKER_SHARE of it: on the 96 GB maintainer's machine they stay 8 GB and
3 GB; on an 8 GB runner with two workers they are 0.8 GB and 2 GB.
"""
import functools
import gc
import os
import re
import subprocess
import sys
import threading

WORKER_CAP_BYTES = 3 * 2**30
FLOOR_BYTES = 8 * 2**30
#: The floor's and the workers' cap's shares of the machine's memory.
FLOOR_SHARE = 0.1
WORKER_SHARE = 0.5
INTERVAL_S = 5.0
_MEMINFO = "/proc/meminfo"

_VM_LINE = re.compile(r"^Pages (free|inactive|speculative|purgeable):\s+(\d+)\.", re.M)
_PAGE = re.compile(r"page size of (\d+) bytes")


def _vm_stat():
    """vm_stat's output, or None where it cannot run (Linux)."""
    try:
        return subprocess.run(["vm_stat"], capture_output=True, text=True,
                              timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return None


def _read_meminfo():
    """/proc/meminfo's text, or None where it is absent (macOS)."""
    try:
        with open(_MEMINFO, encoding="ascii") as fh:
            return fh.read()
    except OSError:
        return None


def _meminfo_bytes(text, key):
    """Bytes on /proc/meminfo's *key* line, or None."""
    m = re.search(r"^%s:\s+(\d+) kB$" % re.escape(key), text or "", re.M)
    return int(m.group(1)) * 1024 if m else None


def available_bytes(vm_stat_text=None, meminfo_text=None):
    """Bytes the system can hand out now: macOS's free, inactive,
    speculative and purgeable pages (vm_stat), else Linux's MemAvailable
    (/proc/meminfo); None where neither can be read."""
    if vm_stat_text is None and meminfo_text is None:
        vm_stat_text = _vm_stat()
        if vm_stat_text is None:
            meminfo_text = _read_meminfo()
    if vm_stat_text is not None:
        m = _PAGE.search(vm_stat_text)
        pages = [int(n) for _k, n in _VM_LINE.findall(vm_stat_text)]
        if not m or not pages:
            return None
        return sum(pages) * int(m.group(1))
    return _meminfo_bytes(meminfo_text, "MemAvailable")


def total_bytes(sysctl_text=None, meminfo_text=None):
    """The machine's memory in bytes: macOS's ``sysctl -n hw.memsize``,
    else Linux's MemTotal; None where neither can be read.  The live
    value is read once a process."""
    if sysctl_text is None and meminfo_text is None:
        return _live_total()
    if sysctl_text is not None:
        s = sysctl_text.strip()
        return int(s) if s.isdigit() else None
    return _meminfo_bytes(meminfo_text, "MemTotal")


@functools.lru_cache(maxsize=1)
def _live_total():
    try:
        out = subprocess.run(["sysctl", "-n", "hw.memsize"],
                             capture_output=True, text=True,
                             timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        out = ""
    return total_bytes(sysctl_text=out) \
        or total_bytes(meminfo_text=_read_meminfo() or "")


def floor_for(total, floor=FLOOR_BYTES, share=FLOOR_SHARE):
    """The watchdog's floor on a machine of *total* bytes (None: unknown):
    *floor* or *share* of *total*, whichever is less."""
    return floor if not total else min(floor, int(total * share))


def worker_cap(total, workers, cap=WORKER_CAP_BYTES, share=WORKER_SHARE):
    """A worker's cap on a machine of *total* bytes shared by *workers*
    (None: one): *cap* or the worker's part of *share* of *total*,
    whichever is less."""
    if not total:
        return cap
    return min(cap, int(total * share / max(1, workers or 1)))


def _worker_count():
    """The run's xdist workers (PYTEST_XDIST_WORKER_COUNT), else 1."""
    try:
        return int(os.environ.get("PYTEST_XDIST_WORKER_COUNT", "1"))
    except ValueError:
        return 1


def rss_bytes(pid=None):
    """The resident size of process *pid* (this one by default), or None."""
    try:
        out = subprocess.run(["ps", "-o", "rss=", "-p", str(pid or os.getpid())],
                             capture_output=True, text=True, timeout=5).stdout
        return int(out.strip()) * 1024
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def clear_caches(modules):
    """Empty every module-level cache of *modules*: dicts whose names hold
    CACHE, and functions carrying functools' cache_clear.  Returns how many
    were emptied."""
    n = 0
    for mod in modules:
        for name, val in list(vars(mod).items()):
            if isinstance(val, dict) and "CACHE" in name and val:
                val.clear()
                n += 1
            elif callable(getattr(val, "cache_clear", None)) \
                    and getattr(val, "__module__", None) == mod.__name__:
                val.cache_clear()
                n += 1
    return n


def _test_modules():
    here = os.path.dirname(os.path.abspath(__file__))
    return [m for m in list(sys.modules.values())
            if getattr(m, "__file__", None)
            and os.path.dirname(os.path.abspath(m.__file__)) == here]


def trim_worker(cap=None, rss=None):
    """Drop the test modules' caches when this process is over *cap*
    (None: the machine's worker_cap); returns True when it did."""
    if cap is None:
        cap = worker_cap(total_bytes(), _worker_count())
    rss = rss_bytes() if rss is None else rss
    if rss is None or rss <= cap:
        return False
    clear_caches(_test_modules())
    gc.collect()
    return True


def too_low(avail, floor=FLOOR_BYTES):
    """True when *avail* bytes (None: unknown) is below *floor*."""
    return avail is not None and avail < floor


def _children(pid):
    try:
        out = subprocess.run(["pgrep", "-P", str(pid)], capture_output=True,
                             text=True, timeout=5).stdout
        return [int(p) for p in out.split()]
    except (OSError, subprocess.SubprocessError, ValueError):
        return []


def _stop_message(avail, floor):
    return ("\nmemory_guard: the machine has %.1f GB available, under the "
            "%.1f GB floor; stopping the test run before the system runs "
            "out.\n" % (avail / 2**30, floor / 2**30))


def _stop(avail, floor=FLOOR_BYTES):
    sys.stderr.write(_stop_message(avail, floor))
    sys.stderr.flush()
    for pid in _children(os.getpid()):
        try:
            os.kill(pid, 9)
        except OSError:
            pass
    os._exit(3)


#: Whether this process's watchdog was started (conftest._start_memory_guard).
_STARTED = False


def start_watchdog(interval=INTERVAL_S, floor=None, stop=None):
    """Start the controlling process's memory check (a daemon thread); it
    runs until *stop* (a ``threading.Event``) is set, or for the process's
    life without one.  *floor* None: the machine's floor_for."""
    stop = stop or threading.Event()
    if floor is None:
        floor = floor_for(total_bytes())

    def run():
        while not stop.is_set():
            avail = available_bytes()
            if too_low(avail, floor):
                _stop(avail, floor)
            stop.wait(interval)
    t = threading.Thread(target=run, name="dash-memory-guard", daemon=True)
    t.start()
    return t
