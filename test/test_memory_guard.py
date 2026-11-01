"""memory_guard: a test run stops before it exhausts the machine's memory
(01nov2026: a full run's workers held about 22 GB and macOS restarted)."""
import functools
import os
import types

import memory_guard as mg

_VM = """Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                                  1000.
Pages active:                                5000.
Pages inactive:                               200.
Pages speculative:                             50.
Pages throttled:                                0.
Pages wired down:                             900.
Pages purgeable:                               10.
"""


def test_available_bytes_reads_vm_stat():
    assert mg.available_bytes(_VM) == (1000 + 200 + 50 + 10) * 16384
    assert mg.available_bytes("nothing here") is None
    live = mg.available_bytes()
    assert live is None or live > 0


def test_rss_bytes_reads_this_process():
    assert mg.rss_bytes() > 10 * 2**20
    assert mg.rss_bytes(pid=os.getpid()) > 0


def test_clear_caches_empties_only_caches():
    mod = types.ModuleType("fake_mod")

    @functools.lru_cache(maxsize=None)
    def built(x):
        return [x]
    built.__module__ = "fake_mod"
    built(1)
    mod.built = built
    mod._PAIR_CACHE = {"a": 1}
    mod._TRUTH = {"kept": 1}
    mod._EMPTY_CACHE = {}
    assert mg.clear_caches([mod]) == 2
    assert mod._PAIR_CACHE == {} and mod._TRUTH == {"kept": 1}
    assert built.cache_info().currsize == 0


def test_trim_worker_acts_only_over_the_cap():
    assert mg.trim_worker(cap=100, rss=50) is False
    assert mg.trim_worker(cap=100, rss=None) is False or mg.rss_bytes() is not None
    assert mg.trim_worker(cap=100, rss=200) is True


def test_too_low():
    assert mg.too_low(1, floor=2) and not mg.too_low(3, floor=2)
    assert not mg.too_low(None, floor=2)


def test_children_and_test_modules():
    assert mg._children(os.getpid()) == [] or all(isinstance(p, int)
                                                  for p in mg._children(os.getpid()))
    assert any(m.__name__ == "memory_guard" for m in mg._test_modules())


def test_start_watchdog_runs_without_stopping_when_memory_is_plenty():
    t = mg.start_watchdog(interval=0.01, floor=0)
    assert t.daemon and t.is_alive()
