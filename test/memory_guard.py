"""Keep a pytest run from exhausting the machine's memory.

On 01nov2026 a full run's eight workers held about 22 GB beside the
maintainer's other work and macOS ran out of memory and restarted.  Two
guards, both wired in conftest.py:

- trim_worker(): after each test module, a worker that has grown past
  WORKER_CAP_BYTES drops every test module's build caches (module-level
  dicts whose names hold CACHE, and functools caches) and collects.
- start_watchdog(): the controlling process reads the machine's available
  memory every few seconds; below FLOOR_BYTES it stops the workers and the
  run, saying why, before the system has to.
"""
import gc
import os
import re
import subprocess
import sys
import threading

WORKER_CAP_BYTES = 3 * 2**30
FLOOR_BYTES = 8 * 2**30
INTERVAL_S = 5.0

_VM_LINE = re.compile(r"^Pages (free|inactive|speculative|purgeable):\s+(\d+)\.", re.M)
_PAGE = re.compile(r"page size of (\d+) bytes")


def available_bytes(vm_stat_text=None):
    """Bytes the system can hand out now (free, inactive, speculative and
    purgeable pages, from macOS's vm_stat); None where vm_stat is absent."""
    if vm_stat_text is None:
        try:
            vm_stat_text = subprocess.run(["vm_stat"], capture_output=True,
                                          text=True, timeout=5).stdout
        except (OSError, subprocess.SubprocessError):
            return None
    m = _PAGE.search(vm_stat_text or "")
    pages = [int(n) for _k, n in _VM_LINE.findall(vm_stat_text or "")]
    if not m or not pages:
        return None
    return sum(pages) * int(m.group(1))


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


def trim_worker(cap=WORKER_CAP_BYTES, rss=None):
    """Drop the test modules' caches when this process is over *cap*;
    returns True when it did."""
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


def _stop(avail):
    sys.stderr.write(
        "\nmemory_guard: the machine has %.1f GB available, under the %.0f GB "
        "floor; stopping the test run before the system runs out.\n"
        % (avail / 2**30, FLOOR_BYTES / 2**30))
    sys.stderr.flush()
    for pid in _children(os.getpid()):
        try:
            os.kill(pid, 9)
        except OSError:
            pass
    os._exit(3)


def start_watchdog(interval=INTERVAL_S, floor=FLOOR_BYTES):
    """Start the controlling process's memory check (a daemon thread)."""
    def run():
        while True:
            avail = available_bytes()
            if too_low(avail, floor):
                _stop(avail)
            threading.Event().wait(interval)
    t = threading.Thread(target=run, name="dash-memory-guard", daemon=True)
    t.start()
    return t
