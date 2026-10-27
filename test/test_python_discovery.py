"""test_python_discovery.py -- dash runs the Python Stata finds or the user
sets (WP-36 plat:PT-1, ruling M8).

With no ``python set exec`` typed, ``c(python_exec)`` is empty, and Stata
finds a Python itself the first time a ``python:`` line runs (help python).
dash and dash_setup used to refuse that state -- "Python is required but is
not available to Stata", r(198) -- and both sent the user to dash_setup,
which refused the same way.  Under M8 nothing decides whether Python is
there: dash and dash_setup run the ``python:`` lines they run anyway, and a
Python that cannot start is reported with Stata's own message, then dash's
advice, and Stata's return code.  The certification harness follows the
same rule: no script skips or exits for want of a ``c(python_exec)`` value.

These are reads of the shipped text; the behaviour in a fresh HOME is
test_python_discovery_fresh_home.py (release tier), and the advice and the
name dash gives the Python are test_env_guards.cscript Q3601-6..8.
"""
import glob
import importlib.util
import os
import re
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASH_ADO = os.path.join(ROOT, "dash.ado")
SETUP_ADO = os.path.join(ROOT, "dash_setup.ado")
SETUP_LIB = os.path.join(ROOT, "dash_setup_lib.py")
PYEXEC_SH = os.path.join(ROOT, "scripts", "stata_python_exec.sh")

#: The skip gate every Python-dependent script carried (TR-36-01.5).
_GATE = re.compile(
    r"^[ \t]*if `?\"?`c\(python_exec\)'\"?'? == \"\" \{\n"
    r"[ \t]*display as (?:error|text) "
    r"\"(?:SKIP:[^\"\n]*|[^\"\n]*\(c\(python_exec\) is empty\))\"\n"
    r"[ \t]*exit (?:222|601|198)\n[ \t]*\}[ \t]*\n", re.M)
#: Any `if' line that branches on the setting, either way.
_BRANCH = re.compile(r"^[ \t]*if\b[^\n]*c\(python_exec\)[^\n]*(?:==|!=) *\"\"",
                     re.M)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _code(src):
    """Source lines with // comments, * comment lines and *! headers
    removed (the pattern of test_cscript_hygiene.py's ``_code``)."""
    out = []
    for line in src.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        out.append(line.split("//", 1)[0])
    return out


def _program(src, name):
    """The code lines of ``program define <name>`` up to its ``end``."""
    lines = _code(src)
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^\s*program\s+define\s+%s\b" % re.escape(name), line):
            start = i
            break
    assert start is not None, f"program {name} not found"
    for j in range(start + 1, len(lines)):
        if lines[j].strip() == "end":
            return lines[start + 1:j]
    raise AssertionError(f"program {name} has no end")


class TestNoPreCheck:

    def test_require_python_refuses_nothing(self):
        body = [l.strip() for l in _program(_read(DASH_ADO),
                                            "_dash_require_python")
                if l.strip()]
        assert not [l for l in body if l.startswith("exit")
                    or l.startswith("display")], body
        assert body == ["version 19"], body

    def test_the_retry_is_noisy_and_hands_on_the_code(self):
        body = [l.strip() for l in _program(_read(DASH_ADO),
                                            "_dash_require_deps")
                if l.strip()]
        vprobe = [i for i, l in enumerate(body)
                  if "python:" in l and '"_dd_v"' in l]
        assert len(vprobe) == 2, body
        first, retry = (body[i] for i in vprobe)
        assert first.startswith("capture python:"), first
        assert retry.startswith("capture noisily python:"), retry
        assert '"_dd_x", sys.executable' in first, first
        assert retry.split(":", 1)[1] == first.split(":", 1)[1]
        rest = body[vprobe[1] + 1:]
        assert rest[0] == "local _dd_prc = _rc", rest[:3]
        failed = [l for l in rest if l.startswith("_dash_python_failed")]
        assert failed == ['_dash_python_failed `_dd_prc\' `"`c(python_exec)\'"\''], failed
        # The decision is still made from the value, never from _rc.
        assert sum("_rc" in l for l in body) == 1, body

    def test_no_file_says_python_is_unavailable(self):
        for path in (DASH_ADO, SETUP_ADO):
            code = "\n".join(_code(_read(path)))
            for said in ("Python is required but is not available",
                         "Python is not available to Stata"):
                assert said not in code, (os.path.basename(path), said)

    def test_setup_does_not_stop_on_an_empty_setting(self):
        lines = _code(_read(SETUP_ADO))
        stops = []
        for i, line in enumerate(lines):
            if not (_BRANCH.match(line) and '== ""' in line):
                continue
            # The block the `if' opens, to its closing brace.
            depth, j = 0, i
            while j < len(lines):
                depth += lines[j].count("{") - lines[j].count("}")
                if re.match(r"^\s*exit\b", lines[j]):
                    stops.append((i + 1, line.strip()))
                if depth <= 0 and j > i:
                    break
                j += 1
        assert not stops, stops
        assert "Python (not linked to Stata)" not in "\n".join(lines)

    def test_setup_pystart_retries_noisily_and_names_the_python(self):
        body = [l.strip() for l in _program(_read(SETUP_ADO),
                                            "_dash_setup_pystart")
                if l.strip()]
        py = [l for l in body if "python:" in l]
        assert len(py) == 2, body
        assert py[0].startswith("capture python:"), py[0]
        assert py[1].startswith("capture noisily python:"), py[1]
        for line in py:
            assert 'Macro.setLocal("pyexe", sys.executable)' in line, line
        assert "return local pyexe `\"`pyexe'\"'" in body, body


@pytest.fixture
def lib(monkeypatch, tmp_path):
    store = {"exec": "", "pwd": str(tmp_path)}

    class SFIToolkit:
        @staticmethod
        def macroExpand(s):
            return {"\x60c(python_exec)'": store["exec"],
                    "\x60c(pwd)'": store["pwd"]}[s]

    mod = types.ModuleType("sfi")
    mod.SFIToolkit = SFIToolkit
    monkeypatch.setitem(sys.modules, "sfi", mod)
    spec = importlib.util.spec_from_file_location("dash_setup_lib_pd", SETUP_LIB)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.store = store
    return m


class TestLinked:

    def test_empty_setting_is_sys_executable(self, lib):
        lib.store["exec"] = ""
        assert lib._linked() == (sys.executable, "")

    def test_a_set_path_is_resolved(self, lib, tmp_path):
        (tmp_path / "bin").mkdir()
        (tmp_path / "bin" / "python").write_text("")
        lib.store["exec"] = os.path.join("bin", "python")
        assert lib._linked() == (str(tmp_path / "bin" / "python"),
                                 os.path.join("bin", "python"))
        lib.store["exec"] = "/opt/q3601/bin/python3"
        assert lib._linked() == ("/opt/q3601/bin/python3",
                                 "/opt/q3601/bin/python3")


def _harness():
    files = (glob.glob(os.path.join(ROOT, "test", "*.cscript"))
             + [os.path.join(ROOT, "test", "cert_svg.do")]
             + glob.glob(os.path.join(ROOT, "test", "templates", "*.cscript"))
             + glob.glob(os.path.join(ROOT, "scripts", "extract_*.do")))
    return sorted(files)


class TestTheHarness:

    def test_no_script_gates_on_the_setting(self):
        files = _harness()
        assert len(files) > 100, len(files)
        gated = [os.path.relpath(p, ROOT) for p in files
                 if _GATE.search(_read(p)) or _BRANCH.search(_read(p))]
        assert not gated, gated

    def test_stata_python_exec_reads_sys_executable(self):
        src = _read(PYEXEC_SH)
        doc = src.split("<<'EOT'", 1)[1].split("\nEOT", 1)[0]
        assert "sys.executable" in doc, doc
        assert "python query" not in doc, doc
