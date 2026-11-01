"""The server app builder reads each copied helper's text once (WP-30 A2).

``ServerAppBuilder`` copies about 410 of dash_render.py's functions, three
classes and a slice of the module's own text into every app it writes.
Reading them through ``inspect.getsource`` was two thirds of a build (0.11
of 0.166 s, measured 07oct2026); ``_dash_source_of`` keeps each text with
the object it belongs to and the stamp of the file it came from, and reads
it again only when the object or the file is not the one it read.

These pin that the text is ``inspect.getsource``'s, that it is read once,
that a new object or an edited file is read anew, that a build writes the
same app whether the cache is cold, warm or bypassed, and that a reloaded
renderer writes its new text.
"""
import importlib
import importlib.util
import inspect
import os
import shutil
import sys
import time

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402


def _counting_getsource(monkeypatch):
    """Count the calls ``inspect.getsource`` gets from here on."""
    calls = []
    real = inspect.getsource

    def counted(obj):
        calls.append(obj)
        return real(obj)

    monkeypatch.setattr(inspect, "getsource", counted)
    return calls


def _write_module(path, body):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    # A second write in the same clock tick would keep the stamp's time; a
    # different size alone already differs, and the time is moved on too.
    later = time.time() + 5
    os.utime(path, (later, later))


def _import_from(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _build(tmp_path, renderer=dr, plots=None):
    """The source of the app *renderer* builds for a one-layer spec."""
    spec = tp._spec(plots or [plot_for("lfit")])
    _tag, sp, dp = tp._write(spec)
    out = tmp_path / ("app_%d.py" % len(os.listdir(tmp_path)))
    renderer.ServerAppBuilder(sp, dp).build(str(out))
    return out.read_text(encoding="utf-8")


class TestTheTextIsInspects:

    @pytest.mark.parametrize("obj", [dr._fit_grid, dr.GlyphMapper,
                                     dr.GlyphMapper._histogram_grid, dr],
                             ids=["function", "class", "staticmethod",
                                  "module"])
    def test_it_is_what_inspect_reads(self, obj):
        assert dr._dash_source_of(obj) == inspect.getsource(obj)

    def test_an_object_with_no_source_file_raises_as_inspect_does(self):
        with pytest.raises(TypeError):
            inspect.getsource(len)
        with pytest.raises(TypeError):
            dr._dash_source_of(len)
        assert id(len) not in dr._DASH_SOURCE_CACHE


class TestItIsReadOnce:

    def test_a_second_read_does_not_ask_inspect(self, monkeypatch):
        dr._DASH_SOURCE_CACHE.pop(id(dr._fit_grid), None)
        calls = _counting_getsource(monkeypatch)
        first = dr._dash_source_of(dr._fit_grid)
        second = dr._dash_source_of(dr._fit_grid)
        assert first == second
        assert calls == [dr._fit_grid]

    def test_a_warm_build_reads_nothing(self, tmp_path, monkeypatch):
        _build(tmp_path)
        calls = _counting_getsource(monkeypatch)
        _build(tmp_path)
        assert calls == []


class TestTheSplitIsKeptWithItsText:
    """``_dash_source_lines_of``: the text's lines, split once per text."""

    def test_the_lines_are_the_texts_and_split_once(self, monkeypatch):
        want = dr._dash_source_of(dr).splitlines()
        dr._DASH_SOURCE_LINES.pop(id(dr), None)
        first = dr._dash_source_lines_of(dr)
        held = dr._DASH_SOURCE_LINES[id(dr)][1]
        second = dr._dash_source_lines_of(dr)
        assert first == second == want
        assert dr._DASH_SOURCE_LINES[id(dr)][1] is held
        first.append("x")
        assert dr._dash_source_lines_of(dr) == want

    def test_a_text_read_anew_is_split_anew(self, tmp_path):
        path = tmp_path / "dash_probe_lines.py"
        _write_module(path, "X = 1\n")
        mod = _import_from(str(path), "dash_probe_lines")
        try:
            assert dr._dash_source_lines_of(mod) == ["X = 1"]
            _write_module(path, "X = 1\nY = 2\n")
            assert dr._dash_source_lines_of(mod) == ["X = 1", "Y = 2"]
        finally:
            sys.modules.pop("dash_probe_lines", None)


class TestTheConstantScan:
    """``_dash_scan_constants`` finds what the two regexes find over the
    joined text, an assignment spanning lines included."""

    @staticmethod
    def _joined(lines):
        import re
        src = "\n".join(lines)
        return (set(re.findall(r"\b_[A-Z][A-Z0-9_]*\b", src)),
                set(re.findall(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(?::[^=\n]+)?=",
                               src, re.MULTILINE)))

    @pytest.mark.parametrize("lines", [
        ["_A = 1", "x = _B + _C", "    y = _D", "def f(): return _E"],
        ["z", "= _F"], ["w\n", "", ": int = _G"], ["a: int = 1\nb=2", "_H"],
        ["pass", "_I"], ["  v", "= 1"], [],
    ], ids=["plain", "split", "split-blank", "multi", "bare", "indent",
            "empty"])
    def test_it_is_the_joined_scan(self, lines):
        assert dr._dash_scan_constants(lines) == self._joined(lines)
        assert dr._dash_scan_constants(lines) == self._joined(lines)

    def test_a_built_app(self, tmp_path):
        lines = _build(tmp_path).split("\n")
        assert dr._dash_scan_constants(lines) == self._joined(lines)


class TestItIsReadAgainWhenItCouldDiffer:

    def test_a_replaced_function_is_read_anew(self, tmp_path, monkeypatch):
        monkeypatch.syspath_prepend(str(tmp_path))
        path = tmp_path / "dash_probe_replace.py"
        _write_module(path, "def f():\n    return 1\n")
        mod = _import_from(str(path), "dash_probe_replace")
        try:
            first = mod.f
            assert dr._dash_source_of(first) == "def f():\n    return 1\n"
            _write_module(path, "def f():\n    return 22\n")
            mod = importlib.reload(mod)
            assert mod.f is not first
            assert dr._dash_source_of(mod.f) == "def f():\n    return 22\n"
        finally:
            sys.modules.pop("dash_probe_replace", None)

    def test_an_edited_file_is_read_again_for_the_same_object(self,
                                                              tmp_path):
        """The same module object, and its file changed under it."""
        path = tmp_path / "dash_probe_edit.py"
        _write_module(path, "X = 1\n")
        mod = _import_from(str(path), "dash_probe_edit")
        try:
            assert dr._dash_source_of(mod) == "X = 1\n"
            _write_module(path, "X = 1\nY = 2\n")
            assert dr._dash_source_of(mod) == inspect.getsource(mod) \
                == "X = 1\nY = 2\n"
        finally:
            sys.modules.pop("dash_probe_edit", None)


class TestABuildWritesTheSameApp:

    def test_cold_warm_and_uncached_builds_agree(self, tmp_path,
                                                 monkeypatch):
        dr._DASH_SOURCE_CACHE.clear()
        cold = _build(tmp_path)
        warm = _build(tmp_path)
        monkeypatch.setattr(dr, "_dash_source_of", inspect.getsource)
        uncached = _build(tmp_path)
        assert cold == warm == uncached

    def test_a_reloaded_renderer_writes_its_new_text(self, tmp_path,
                                                     monkeypatch):
        """A copy of dash_render.py, built from, edited and reloaded: the
        next app carries the edit."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        monkeypatch.syspath_prepend(str(src_dir))
        name = "dash_render_reload_probe"
        copy = src_dir / (name + ".py")
        shutil.copyfile(os.path.join(_ROOT, "dash_render.py"), copy)
        for fname in os.listdir(_ROOT):
            if fname.startswith("dash-") and fname.endswith(".scheme"):
                shutil.copyfile(os.path.join(_ROOT, fname), src_dir / fname)
        apps = tmp_path / "apps"
        apps.mkdir()
        mod = _import_from(str(copy), name)
        try:
            before = _build(apps, mod)
            marker = "    # reload probe: this line was added after a build\n"
            text = copy.read_text(encoding="utf-8")
            head = "def _fit_grid("
            at = text.index(head)
            body = text.index('"""', text.index('"""', at) + 3) + 3
            body = text.index("\n", body) + 1
            _write_module(copy, text[:body] + marker + text[body:])
            mod = importlib.reload(mod)
            after = _build(apps, mod)
            assert marker not in before
            assert marker in after
            assert after.replace(marker, "", 1) == before
        finally:
            sys.modules.pop(name, None)
