"""The data file dash writes from Stata, and what both renderers make of it.

dash.ado exported its data with jsonio, whose ado returns the JSON it wrote
in a macro and expands it inside compound quotes: a string value, value
label or variable label holding an unclosed compound quote or a lone
backtick stopped every export with r(132) "too few quotes", and one holding
the closing pair or a lone apostrophe with r(109) -- whatever the
qualifier, so any dashboard over such data failed; every strL arrived as
the text "null", flagged as a number (measured 24sep2026;
test_string_values.cscript, which holds every value to Stata's bytes
through Stata itself, in both modes).

dash.ado now writes the file through Stata's own Python
(``_dash_write_data``), by dash_render.py's ``_dash_write_stata_data``,
which reads each value through the Stata Function Interface.  This file
holds that function to jsonio's layout with a stand-in for ``sfi``, and the
renderers to every adversarial value it can write (CLAUDE.md rules 16 and
18): markup that would end a script element, text that looks like the
JSON around it, a megabyte string, a strL, and the text "null".
"""
import html
import importlib.util
import json
import os
import re
import sys
import tempfile
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)

import dash_render as dr  # noqa: E402

_ADO = os.path.join(_ROOT, "dash.ado")

#: Every value test_string_values.cscript builds in Stata, and more.
ADVERSARIAL = [
    "`\"hi",                       # an unclosed compound double quote
    "\"'hi",                       # the closing pair
    "a`b",                         # a lone backtick
    "'tick",                       # a lone apostrophe
    "cost $HOME ${x} x",           # a global and a braced global
    "a\\b\\",                      # backslashes, one last
    "say \"hi\"",                  # double quotes
    "l1\r\nl2\n",                  # CR LF and LF
    "b\x01\x07\x1b\x1f\x7fe",      # control bytes
    "café 日本 \U0001F600",   # UTF-8 of two, three, four bytes
    "`c1'",                        # a local's name, which must not expand
    "`=1+1'",                      # an expression, which must not run
    "</script><script>alert(1)</script>",
    "\ttab",
    "`\"hi\"'",
    "\"},\"x\":1,{\\u0000  ",    # the JSON around it, and JS's
    "null",                        # the missing number's text
    "",
    "  x  ",
    "<!--&amp;&#60;",
    "NaN",
    "1e5",
    "﻿bom‮rlo",
    "``''\"\"",
]


# ===========================================================================
# A stand-in for Stata's sfi module
# ===========================================================================

class _BadText(UnicodeDecodeError):
    def __init__(self):
        super().__init__("utf-8", b"\xc8", 0, 1, "invalid continuation byte")


class FakeSfi:
    """The four sfi calls the writer makes, over columns held in Python.

    ``columns`` maps a name to its values; a string column is text, a
    numeric one numbers or None for a missing value.  ``types`` names each
    column's storage type ("str", "strL" or a numeric type).  ``bad`` holds
    (name, obs) cells whose text is not UTF-8; ``binary`` strL cells that
    hold binary data.
    """

    def __init__(self, columns, types, var_labels=None, label_names=None,
                 label_sets=None, bad=(), binary=(), bad_varlabel=(),
                 bad_labelset=()):
        self.columns, self.types = columns, types
        self.order = list(columns)
        self.var_labels = var_labels or {}
        self.label_names = label_names or {}
        self.label_sets = label_sets or {}
        self.bad, self.binary = set(bad), set(binary)
        self.bad_varlabel, self.bad_labelset = set(bad_varlabel), set(bad_labelset)
        fake = self

        class Data:
            @staticmethod
            def getObsTotal():
                return len(next(iter(fake.columns.values()))) if fake.columns else 0

            @staticmethod
            def isVarTypeString(v):
                return fake.types[v] in ("str", "strL")

            @staticmethod
            def isVarTypeStrL(v):
                return fake.types[v] == "strL"

            @staticmethod
            def getVarIndex(v):
                return fake.order.index(v)

            @staticmethod
            def get(var, missingval="default"):
                assert isinstance(var, str) and " " not in var, var
                if any(c[0] == var for c in fake.bad):
                    raise SystemError("returned a result with an exception set")
                vals = list(fake.columns[var])
                if fake.types[var] in ("str", "strL"):
                    return vals
                assert missingval is None, "missing values must come back as None"
                return vals

            @staticmethod
            def getAt(j, i):
                v = fake.order[j]
                if (v, i) in fake.bad:
                    raise _BadText()
                return fake.columns[v][i]

            @staticmethod
            def getVarLabel(v):
                if v in fake.bad_varlabel:
                    raise _BadText()
                return fake.var_labels.get(v, "")

        class ValueLabel:
            @staticmethod
            def getVarValueLabel(v):
                return fake.label_names.get(v, "")

            @staticmethod
            def getValueLabels(name):
                if name in fake.bad_labelset:
                    raise SystemError("returned a result with an exception set")
                return dict(fake.label_sets.get(name, {}))

        class StrLConnector:
            def __init__(self, v, i):
                self.v, self.i = v, i

            def isBinary(self):
                return (self.v, self.i) in fake.binary

        self.globals, self.commands, self.shown = {}, [], []

        class Macro:
            @staticmethod
            def getGlobal(name):
                return fake.globals.get(name, "")

        class SFIToolkit:
            """The Stata commands the writer runs, as Stata would run them.
            A cell, variable label or label set held in ``bad*`` holds the
            text ustrfix() gives; only its direct read raises."""

            @staticmethod
            def displayln(text):
                fake.shown.append(text)

            @staticmethod
            def stata(cmd):
                fake.commands.append(cmd)
                m = re.fullmatch(r"quietly generate strL (\w+) = ustrfix\((\w+)\)", cmd)
                if m:
                    tmp, v = m.groups()
                    assert tmp not in fake.columns
                    fake.columns[tmp] = list(fake.columns[v])
                    fake.types[tmp] = "strL"
                    fake.order.append(tmp)
                    return
                m = re.fullmatch(r"capture drop (\w+)", cmd)
                if m:
                    fake.columns.pop(m.group(1), None)
                    fake.types.pop(m.group(1), None)
                    if m.group(1) in fake.order:
                        fake.order.remove(m.group(1))
                    return
                m = re.fullmatch(r'quietly mata: st_global\("(\w+)", '
                                 r'ustrfix\(st_varlabel\("(\w+)"\)\)\)', cmd)
                if m:
                    fake.globals[m.group(1)] = fake.var_labels.get(m.group(2), "")
                    return
                m = re.fullmatch(r"capture macro drop (\w+)", cmd)
                if m:
                    fake.globals.pop(m.group(1), None)
                    return
                m = re.fullmatch(r'quietly mata: (\w+) = \.; (\w+) = ""; '
                                 r'st_vlload\("(\w+)", \1, \2\); '
                                 r'st_vlmodify\("(\w+)", \1, ustrfix\(\2\)\)', cmd)
                if m:
                    fake.label_sets[m.group(4)] = dict(fake.label_sets[m.group(3)])
                    return
                m = re.fullmatch(r"capture label drop (\w+)", cmd)
                if m:
                    fake.label_sets.pop(m.group(1), None)
                    return
                if re.fullmatch(r"capture mata: mata drop \w+ \w+", cmd):
                    return
                raise AssertionError("unexpected Stata command: %r" % cmd)

        self.Data, self.ValueLabel, self.StrLConnector = Data, ValueLabel, StrLConnector
        self.Macro, self.SFIToolkit = Macro, SFIToolkit


def _write(tmp_path, fake, names, fname="data.json"):
    path = str(tmp_path / fname)
    msg = dr._dash_write_stata_data(path, names, sfi=fake)
    return path, msg


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _fake_auto(values=None, strl=False):
    """rowid, a double y, a byte g with a value label and extended missing
    values, and a string s holding *values*."""
    values = list(ADVERSARIAL if values is None else values)
    n = len(values)
    g = [float(i % 3) for i in range(n)]
    g[1] = None                     # .a
    g[2] = None                     # .
    return FakeSfi(
        {"rowid": list(range(1, n + 1)), "y": [i / 3 for i in range(n)],
         "g": g, "s": values},
        {"rowid": "long", "y": "double", "g": "byte",
         "s": "strL" if strl else "str"},
        var_labels={"s": "`\"label\"' $x", "g": "Group"},
        label_names={"g": "gl"},
        label_sets={"gl": {0: "`\"zero", 1: "\"'one`", ".a": "missing `a",
                           ".z": "zz"}})


# ===========================================================================
# _dash_label_key
# ===========================================================================

class TestTheLabelKey:

    def test_an_integer_is_its_digits(self):
        assert dr._dash_label_key(1) == "1"
        assert dr._dash_label_key(-5) == "-5"
        assert dr._dash_label_key(3.0) == "3"

    def test_an_extended_missing_value_is_jsonios_code(self):
        # jsonio's key for .a, measured 24sep2026: 2147483622.
        assert dr._dash_label_key(".a") == "2147483622"
        assert dr._dash_label_key(".z") == "2147483647"
        assert dr._dash_label_key(".") == "2147483621"

    def test_anything_else_has_no_key(self):
        for bad in (1.5, float("nan"), float("inf"), ".aa", ".A", "x", None,
                    "", ".1"):
            assert dr._dash_label_key(bad) is None, bad


# ===========================================================================
# _dash_write_stata_data: jsonio's layout, every value as Stata holds it
# ===========================================================================

class TestTheWriter:

    def test_the_layout_is_jsonios(self, tmp_path):
        path, msg = _write(tmp_path, _fake_auto(), "rowid y g s")
        assert msg == ""
        d = _load(path)
        assert set(d) == {"values", "firstRecordId", "lastRecordId",
                          "variableIndices", "variableIsString",
                          "variableNames", "variableLabels",
                          "valueLabelNames", "valueLabels",
                          "numberOfRecords", "numberOfVariables"}
        n = len(ADVERSARIAL)
        assert d["numberOfRecords"] == n and d["lastRecordId"] == n
        assert d["firstRecordId"] == 1
        assert d["numberOfVariables"] == 4
        assert d["variableNames"] == ["rowid", "y", "g", "s"]
        assert d["variableIndices"] == [1, 2, 3, 4]
        assert d["variableIsString"] == {"rowid": False, "y": False,
                                         "g": False, "s": True}
        assert list(d["values"][0]) == ["rowid", "y", "g", "s"]

    def test_every_string_is_written_exactly(self, tmp_path):
        path, _ = _write(tmp_path, _fake_auto(), "s")
        got = [r["s"] for r in _load(path)["values"]]
        assert got == ADVERSARIAL

    def test_the_file_is_utf8_and_never_holds_a_raw_script_end(self, tmp_path):
        """json escapes nothing HTML cares about, and need not: the file is
        read by Python only.  What matters is that it is UTF-8 and parses."""
        path, _ = _write(tmp_path, _fake_auto(), "s")
        with open(path, "rb") as fh:
            raw = fh.read()
        raw.decode("utf-8")        # raises if not UTF-8
        assert b"\r" not in raw and b"\n" not in raw   # control bytes escaped

    def test_numbers_are_doubles_and_missing_is_jsonios_null(self, tmp_path):
        path, _ = _write(tmp_path, _fake_auto(), "rowid g")
        vals = _load(path)["values"]
        assert vals[0]["rowid"] == 1.0 and isinstance(vals[0]["rowid"], float)
        assert vals[1]["g"] == "null" and vals[2]["g"] == "null"
        assert vals[3]["g"] == 0.0

    def test_labels_are_written_as_stata_holds_them(self, tmp_path):
        path, _ = _write(tmp_path, _fake_auto(), "g s")
        d = _load(path)
        assert d["variableLabels"] == {"g": "Group", "s": "`\"label\"' $x"}
        assert d["valueLabelNames"] == {"g": "gl"}
        assert d["valueLabels"] == {"g": {"0": "`\"zero", "1": "\"'one`",
                                          "2147483622": "missing `a",
                                          "2147483647": "zz"}}

    def test_a_strl_is_a_string(self, tmp_path):
        """jsonio wrote every strL as "null" and flagged it a number."""
        path, _ = _write(tmp_path, _fake_auto(strl=True), "s")
        d = _load(path)
        assert d["variableIsString"] == {"s": True}
        assert [r["s"] for r in d["values"]] == ADVERSARIAL

    def test_a_name_given_twice_is_written_once(self, tmp_path):
        path, _ = _write(tmp_path, _fake_auto(), "s y s y")
        assert _load(path)["variableNames"] == ["s", "y"]

    def test_no_observations_is_an_empty_file_of_the_same_shape(self, tmp_path):
        fake = FakeSfi({"y": [], "s": []}, {"y": "double", "s": "str"})
        path, msg = _write(tmp_path, fake, "y s")
        d = _load(path)
        assert msg == "" and d["values"] == [] and d["numberOfRecords"] == 0

    def test_text_that_is_not_utf8_is_read_through_ustrfix(self, tmp_path):
        """jsonio wrote each invalid byte as U+FFFD and the page was drawn
        (test_adversarial.cscript P20-28); the writer reads the column
        through Stata's ustrfix(), in a variable it makes and drops, and
        notes it."""
        values = list(ADVERSARIAL)
        values[4] = "caf\ufffd"          # what ustrfix() gives for the cell
        fake = _fake_auto(values)
        fake.bad = {("s", 4)}
        path, msg = _write(tmp_path, fake, "y s")
        assert msg == ""
        assert [r["s"] for r in _load(path)["values"]] == values
        assert list(fake.columns) == ["rowid", "y", "g", "s"]   # dropped
        made = [c for c in fake.commands if c.startswith("quietly generate")]
        assert len(made) == 1 and re.fullmatch(
            r"quietly generate strL __dashfix[0-9a-f]{12} = ustrfix\(s\)",
            made[0])
        assert len(fake.shown) == 1
        assert fake.shown[0].startswith(
            "{txt}dash: string variable s holds text that is not valid UTF-8")
        assert "unicode translate" in fake.shown[0]

    def test_a_binary_strl_is_refused_naming_it(self, tmp_path):
        fake = _fake_auto(strl=True)
        fake.binary = {("s", 2)}
        path, msg = _write(tmp_path, fake, "s")
        assert msg.startswith("dash: strL variable s holds binary data in "
                              "observation 3")
        assert not os.path.exists(path)

    def test_a_label_that_is_not_utf8_is_read_through_ustrfix(self, tmp_path):
        fake = _fake_auto()
        fake.var_labels["s"] = "Mile\ufffdage"
        fake.bad_varlabel = {"s"}
        path, msg = _write(tmp_path, fake, "s")
        assert msg == ""
        assert _load(path)["variableLabels"]["s"] == "Mile\ufffdage"
        assert fake.globals == {}                   # the global is dropped
        assert fake.shown[0].startswith(
            "{txt}dash: the variable label of s holds text that is not valid")
        fake = _fake_auto()
        fake.label_sets["gl"][1] = "For\ufffd"
        fake.bad_labelset = {"gl"}
        path, msg = _write(tmp_path, fake, "g", "d2.json")
        assert msg == ""
        assert _load(path)["valueLabels"]["g"]["1"] == "For\ufffd"
        assert set(fake.label_sets) == {"gl"}       # the copy is dropped
        assert fake.shown[0].startswith(
            "{txt}dash: value label gl, on g, holds text that is not valid")

    def test_a_name_that_is_not_a_stata_name_is_refused(self, tmp_path):
        """Names reach Stata commands (the ustrfix() reads): one holding
        anything but a name's characters is refused before any is run."""
        for bad in ("s;drop", "a`b", "x$y", "q\"", "}", "1abc", "a" * 33):
            fake = _fake_auto()
            fake.columns[bad] = list(fake.columns["s"])
            fake.types[bad] = "str"
            fake.order.append(bad)
            path, msg = _write(tmp_path, fake, "s " + bad)
            assert "is not a variable name the export can read" in msg, bad
            assert fake.commands == [] and not os.path.exists(path)

    def test_the_name_check(self):
        for good in ("s", "_x1", "caf\u00e9", "a" * 32):
            assert dr._dash_is_stata_name(good), good
        for bad in ("", "1a", "a b", "a`", "a$", "a'", "a\"", "a{", "a" * 33,
                    None, 5):
            assert not dr._dash_is_stata_name(bad), bad

    def test_an_undefined_label_set_writes_no_labels(self, tmp_path):
        fake = _fake_auto()
        fake.label_sets = {}
        path, _ = _write(tmp_path, fake, "g")
        d = _load(path)
        assert d["valueLabelNames"] == {"g": "gl"} and d["valueLabels"] == {"g": {}}

    def test_a_megabyte_string_is_written_whole(self, tmp_path):
        big = "<" + "x" * (1 << 20) + "`\">"
        fake = _fake_auto([big, "a", "b"], strl=True)
        path, _ = _write(tmp_path, fake, "s")
        assert _load(path)["values"][0]["s"] == big


# ===========================================================================
# Both renderers, on what the writer writes
# ===========================================================================

def _spec_file(tmp_path):
    spec = {"graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "options": {"name": "g1"},
                        "plots": [{"type": "scatter", "yvar": "y",
                                   "xvar": "rowid", "if_expr": "",
                                   "in_expr": "",
                                   "options": {"mlabel": "s"}}]}],
            "kpis": [],
            "build_options": {"layout": "1 1", "registry": "g1",
                              "formats": {}}}
    sp = str(tmp_path / "spec.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    return sp


def _served_frame(sp, dp, tmp_path):
    ap = str(tmp_path / "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with open(ap, encoding="utf-8") as fh:
        src = fh.read()
    attach = "if __name__ != '__main__':\n    make_document(curdoc())"
    assert attach in src
    ns = {"__name__": "_sv_app"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        exec(compile(src.replace(attach, "pass"), ap, "exec"), ns)
        _spec, df, meta = ns["_load_spec_and_data"]()
    return src, df, meta


@pytest.mark.parametrize("strl", [False, True], ids=["str", "strL"])
class TestBothRenderersLoadEveryValueExactly:

    def test_saved_and_served(self, tmp_path, strl):
        dp, msg = _write(tmp_path, _fake_auto(strl=strl), "rowid y g s")
        assert msg == ""
        sp = _spec_file(tmp_path)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
        assert list(r.df["s"]) == ADVERSARIAL
        assert "s" in r.string_vars
        assert r.variable_labels["s"] == "`\"label\"' $x"
        src, df, meta = _served_frame(sp, dp, tmp_path)
        assert list(df["s"]) == ADVERSARIAL
        assert meta["var_labels"]["s"] == "`\"label\"' $x"
        assert meta["val_labels"]["g"]["1"] == "\"'one`"
        # "null" as a string is text, never a missing value.
        assert r.df["s"][16] == "null" and df["s"][16] == "null"
        # The app carries the data base64-encoded: no value is source text.
        assert "alert(1)" not in src and "$HOME" not in src

    def test_missing_numbers_are_missing_in_both(self, tmp_path, strl):
        dp, _ = _write(tmp_path, _fake_auto(strl=strl), "rowid y g s")
        sp = _spec_file(tmp_path)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
        _src, df, _meta = _served_frame(sp, dp, tmp_path)
        for frame in (r.df, df):
            assert frame["g"].isna().tolist()[:4] == [False, True, True, False]


class TestThePageCarriesNoValueAsMarkup:

    def test_a_script_end_in_a_value_stays_inside_the_json(self, tmp_path):
        """The value is embedded, as data, in the page's JSON script
        element, HTML-escaped by Bokeh: the page parses back to the value,
        and the markup it holds never appears raw."""
        dp, _ = _write(tmp_path, _fake_auto(), "rowid y g s")
        sp = _spec_file(tmp_path)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            page = dr.DashRenderer(sp, dp).render()
        assert "<script>alert(1)" not in page
        assert "<!--&amp;" not in page
        blocks = re.findall(r'<script type="application/json"[^>]*>(.*?)</script>',
                            page, re.S)
        assert blocks
        strings, stack = set(), [json.loads(html.unescape(b)) for b in blocks]
        while stack:
            v = stack.pop()
            if isinstance(v, str):
                strings.add(v)
            elif isinstance(v, dict):
                stack.extend(v.values())
            elif isinstance(v, list):
                stack.extend(v)
        for value in ("</script><script>alert(1)</script>", "`\"hi",
                      "<!--&amp;&#60;"):
            assert value in strings, value


# ===========================================================================
# dash.ado exports through the writer, and never through jsonio
# ===========================================================================

def _ado():
    with open(_ADO, encoding="utf-8") as fh:
        return fh.read()


class TestDashAdoUsesTheWriter:

    def test_both_routes_call_the_writer_and_neither_calls_jsonio(self):
        code = "\n".join(l.split("//", 1)[0] for l in _ado().splitlines())
        assert len(re.findall(r"^\s*capture noisily _dash_write_data\b",
                              code, re.M)) == 2
        assert not re.search(r"\bjsonio\s+out\b", code)
        assert "which jsonio" not in code

    def test_every_entry_point_is_called_by_the_ado_and_no_other(self):
        called = set(re.findall(r"_dash_xm\.(_dash_\w+)\(", _ado()))
        declared = {f.__name__ for f in dr._DASH_ADO_ENTRY_POINTS}
        assert called == declared == {"_dash_write_stata_data"}

    def test_names_and_path_reach_python_by_value(self):
        """The path and the variable names are read by Macro.getLocal(),
        never spliced into Python source."""
        prog = _ado().split("program define _dash_write_data", 1)[1]
        prog = prog.split("\nend\n", 1)[0]
        py = [l.strip() for l in prog.splitlines()
              if l.strip().startswith("python:")]
        assert py, "the writer's python: lines moved"
        for line in py:
            assert "`" not in line and "$" not in line, line
        assert 'getLocal("_dw_path")' in prog and 'getLocal("_dw_vars")' in prog
