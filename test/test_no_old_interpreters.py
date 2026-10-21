"""No test or script names a Python interpreter below 3.11.

The maintainer ruled (21oct2026) that nothing runs a Python below dash's
floor: /usr/bin/python3 is 3.9 on macOS, and the framework 2.7/3.x installs
abort at start-up under this host's empty PYTHONHOME.  A child Python is
sys.executable or a 3.11+ path.
"""
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OLD = re.compile(r"/usr/bin/python|\bpython2\b|\bpython3\.(?:[0-9]|10)(?![0-9])"
                  r"|Versions/(?:2\.\d+|3\.(?:[0-9]|10))/")
_EXT = (".py", ".sh", ".do", ".cscript", ".ado")


def _files():
    yield os.path.join(_ROOT, "Makefile")
    for d in ("test", "scripts"):
        for base, dirs, names in os.walk(os.path.join(_ROOT, d)):
            dirs[:] = [x for x in dirs if x not in ("__pycache__", "fixtures", ".cache")]
            for n in names:
                if n.endswith(_EXT) and n != "test_no_old_interpreters.py":
                    yield os.path.join(base, n)


def _hits(text):
    return [i + 1 for i, line in enumerate(text.split("\n")) if _OLD.search(line)]


def test_the_pattern_finds_an_old_interpreter_and_passes_a_new_one():
    assert _hits('run(["/usr/bin/python3", "-V"])') == [1]
    assert _hits("/usr/local/bin/python3.6 -B") == [1]
    assert _hits("python3.10 -m pip") == [1]
    assert _hits("/Library/Frameworks/Python.framework/Versions/2.7/bin/python") == [1]
    assert _hits("/opt/homebrew/bin/python3.13 and python3.11") == []


def test_no_test_or_script_names_an_interpreter_below_the_floor():
    bad = []
    for path in _files():
        with open(path, encoding="utf-8", errors="replace") as f:
            for n in _hits(f.read()):
                bad.append("%s:%d" % (os.path.relpath(path, _ROOT), n))
    assert not bad, bad
