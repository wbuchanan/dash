"""tsline's time-axis options as twoway reads them (WP-30 P1.6, section 51).

The defect (DROPIN-REMAINING.md P1.6; GAPS2.md A4, B14): ``tlabel()``,
``ttick()``, ``tmlabel()``, ``tmtick()``, ``ttitle()``, ``tscale()`` and
``tline()`` were undeclared, fell to the catch-all and were only named in the
note: ``dash tsline y, tlabel(2000m1(12)2004m1) ttitle("Month")
tline(2002m1)`` drew neither labels, title nor line.  twoway folds them onto
the x axis after the x options, reading each date literal in the unit of
the axis's label format (``2002m1`` is 504 on a ``%tm`` axis).

dash folds them at registration (dash.ado ``_dash_taxis_fold``; Mata
``_dash_taxis_unit``, ``_dash_tdate_value``, ``_dash_tdate_ticks``,
``_dash_tdate_lines``, ``_dash_tdate_range``, ``_dash_xdate_find``), so the
spec carries only x keys and the unchanged renderer draws them in both
modes.  The fold itself is checked against live twoway in
test/test_twoway_option_parity.cscript (TA-01 ..); this file holds the
drawing of the folded keys against twoway's truth
(test/fixtures/taxis_truth.json, scripts/extract_taxis_truth.do), the
declarations, the security scan, the records and the help.

While iterating run only this file (CLAUDE.md rule 10):
``python3 -m pytest test/test_taxis_options.py -q``.
"""
import json
import os
import re
import sys
import tempfile

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from bokeh.models import DatetimeAxis, GlyphRenderer, Plot, Span  # noqa: E402
from test_date_range import _filter, _saved, _served, _spec  # noqa: E402
from test_saved_filter_layers import _move  # noqa: E402
from test_served_filter_move import _move as _served_move  # noqa: E402

_FIX = json.load(open(os.path.join(_ROOT, "test", "fixtures",
                                   "taxis_truth.json"), encoding="utf-8"))
_P = _FIX["probes"]
MODES = ("saved", "served")

#: The 60 months of the extractor: t = 2000m1 .. 2004m12 (480 .. 539).
_TS = pd.DataFrame({"t": [480.0 + i for i in range(60)],
                    "y": [101.0 + i for i in range(60)],
                    "z": [50.0 + (i % 7) for i in range(60)],
                    "n": [1.0 + i for i in range(60)],
                    "d": [float(14610 + 30 * i) for i in range(60)],
                    "g": [float(i % 2) for i in range(60)]})
_FMT = {"t": "%tm", "d": "%td"}
_TSLINE = {"type": "tsline", "yvar": "y", "xvar": "t", "options": {}}

#: The x keys dash writes for each probe's t-options (TA-01 pins the same
#: values from live dash against live twoway).
_FOLDED = {
    "c01": {"xlabel": "480 492 504 516 528"},
    "c05": {"xtitle": '"Month"'},
    "c06": {"xscale": "range(468 552)"},
    "c07": {"xline": "504"},
    "c08": {"xline": "492 516"},
    "c09": {"xline": "492 504 516"},
}
#: c01 + c05 + c07 folded together.
_ALL = {"xlabel": "480 492 504 516 528", "xtitle": '"Month"', "xline": "504"}


def _stata(ms, fig):
    """A position on *fig*'s x axis in Stata units."""
    if any(isinstance(a, DatetimeAxis) for a in fig.below):
        return round(dr._dash_unix_ms_to_unit(ms, "m"), 3)
    return round(float(ms), 3)


def _figs(models):
    return [m for m in models if isinstance(m, Plot)
            and any(isinstance(r, GlyphRenderer) for r in m.renderers)]


def _build(tmp_path, mode, plots, go, filt=None):
    """(the root or document, drawn figures) for one spec in one mode."""
    spec = _spec(plots, formats=_FMT, graph_options=go,
                 filters=[_filter("dropdown", filt)] if filt else None)
    d = tempfile.mkdtemp(dir=str(tmp_path))
    if mode == "saved":
        r, _w = _saved(d, spec, _TS)
        return r, _figs(r._last_layout_root.references())
    doc, _w = _served(d, spec, _TS)
    return doc, _figs([m for root in doc.roots for m in root.references()])


def _read(fig):
    """(major ticks, extra ticks, Span positions, title, (lo, hi)) of x."""
    (ax,) = [a for a in fig.below if hasattr(a, "ticker")]
    t = ax.ticker
    base = t.args["base"].ticks if hasattr(t, "args") else t.ticks
    extra = t.args.get("extra", []) if hasattr(t, "args") else []
    spans = [s.location for s in fig.center
             if isinstance(s, Span) and s.dimension == "height"]
    return ([_stata(v, fig) for v in base], [_stata(v, fig) for v in extra],
            sorted(_stata(v, fig) for v in spans), ax.axis_label,
            (_stata(fig.x_range.start, fig), _stata(fig.x_range.end, fig)))


def _source(path):
    with open(os.path.join(_ROOT, path), encoding="utf-8") as fh:
        return fh.read()


def _program(src, name):
    """The body of ado program *name*."""
    m = re.search(r"^program define %s\b.*?^end\b" % re.escape(name), src,
                  re.S | re.M)
    assert m, name
    return m.group(0)


def _mata_fn(src, name):
    """The body of Mata function *name* (its signature line to the brace
    that closes it)."""
    m = re.search(r"^[a-z][a-z ]*\b%s\(" % re.escape(name), src, re.M)
    assert m, name
    i = src.index("{", m.end())
    depth = 0
    for j in range(i, len(src)):
        depth += {"{": 1, "}": -1}.get(src[j], 0)
        if depth == 0:
            return src[m.start():j + 1]
    raise AssertionError(name)


_T_OPTS = ("tlabel", "ttick", "tmlabel", "tmtick", "tscale", "ttitle",
           "tline")
_T_DECL = ("TLabel", "TTICk", "TMLabel", "TMTick", "TSCale", "TTitle",
           "TLIne")
_T2 = ("tlabel2", "ttick2", "tline2", "tscale2", "ttitle2")
_MATA = ("_dash_taxis_unit", "_dash_tdate_value", "_dash_tdate_ticks",
         "_dash_tdate_lines", "_dash_tdate_range", "_dash_xdate_find")


class TestTheFixture:
    def test_it_is_stamped(self):
        meta = _FIX["_meta"]
        assert set(meta) >= {"stata_version", "born_date", "dash_commit",
                             "extracted"}
        assert meta["stata_version"].startswith("19.")
        ids = {"c00", "c01", "c05", "c06", "c07", "c11", "c12", "c13",
               "e01", "e04", "e05", "f01", "f09", "f10", "g01", "g02",
               "g03", "k01", "k03", "k04", "m8", "ab_tm", "ab_ts", "c2_d1",
               "pc2", "op1", "xl1", "xsc1"}
        assert ids <= set(_P), sorted(ids - set(_P))
        assert sum(k.startswith("m6_") for k in _P) == 80
        assert _P["c01"]["ticks"] == [480, 492, 504, 516, 528]
        assert (_P["f01"]["rc"], _P["m8"]["rc"]) == (198, 123)


class TestTheDeclarations:
    def test_declared_returned_and_listed(self):
        src = _source("dash.ado")
        bad = []
        for prog in ("_dash_parse_graph_opts", "_dash_parse_plot_opts"):
            body = _program(src, prog)
            for opt, decl in zip(_T_OPTS, _T_DECL):
                if not re.search(r"\b%s\(string asis\)" % decl, body):
                    bad.append(f"{prog}: no {decl}(string asis)")
                pre = "g_" if prog == "_dash_parse_plot_opts" else ""
                if not re.search(r"sreturn local %s%s\s+: copy local %s\b"
                                 % (pre, opt, opt), body):
                    bad.append(f"{prog}: no sreturn of {opt}")
            # Flipped (WP-31 D1): "pending" was wrong once minor ticks and
            # labels are drawn; tmlabel() and tmtick() are named nowhere.
            for opt in ("tmlabel", "tmtick"):
                if f"length local {opt}' local _dash_pending" in body:
                    bad.append(f"{prog}: {opt} pending")
        lists = re.findall(r"foreach gk(?:ey)? in (.*?)\{", src, re.S)
        lists = [l for l in lists if "xmlabel" in l]
        if len(lists) != 7:
            bad.append(f"{len(lists)} key lists")
        for i, l in enumerate(lists):
            words = l.replace("///", " ").split()
            for opt in _T_OPTS:
                if opt not in words:
                    bad.append(f"key list {i + 1} lacks {opt}")
        assert not bad, bad

    def test_the_axis2_forms(self):
        """dash's spellings of the axis(2) forms, as XLABEL2 is: declared
        in both blocks, returned and in the seven key lists."""
        src = _source("dash.ado")
        bad = []
        for prog in ("_dash_parse_graph_opts", "_dash_parse_plot_opts"):
            body = _program(src, prog)
            pre = "g_" if prog == "_dash_parse_plot_opts" else ""
            for opt in _T2:
                if not re.search(r"\b%s\(string asis\)" % opt.upper(), body):
                    bad.append(f"{prog}: no {opt.upper()}(string asis)")
                if not re.search(r"sreturn local %s%s\s+: copy local %s\b"
                                 % (pre, opt, opt), body):
                    bad.append(f"{prog}: no sreturn of {opt}")
        lists = [l for l in re.findall(r"foreach gk(?:ey)? in (.*?)\{", src,
                                       re.S) if "xmlabel" in l]
        for i, l in enumerate(lists):
            words = l.replace("///", " ").split()
            bad += [f"key list {i + 1} lacks {o}" for o in _T2
                    if o not in words]
        assert not bad, bad


class TestNoStataCallTakesUserText:
    def test_static_scan(self):
        """No date token reaches _stata(), stata() or a regular expression
        in the converter, and the fold builds one command line only, a
        numlist over the numbers the converter wrote."""
        msrc = _source("dash_parse.mata")
        bad = []
        for fn in _MATA:
            body = _mata_fn(msrc, fn)
            for word in ("_stata(", "stata(", "regexm", "regexr"):
                if word in body:
                    bad.append(f"{fn} holds {word}")
        fold = _program(_source("dash.ado"), "_dash_taxis_fold")
        for word in ("_stata(", " stata(", "regexm"):
            if word in fold:
                bad.append(f"_dash_taxis_fold holds {word}")
        for ln in fold.splitlines():
            s = ln.split("//")[0].strip()
            if re.search(r"(^|\s)numlist\s", s) and "_tf_nl'" not in s:
                bad.append(f"numlist over other text: {s}")
        assert any("numlist" in ln and "_tf_nl'" in ln
                   for ln in fold.splitlines()), "no numlist on _tf_nl"
        assert not bad, bad


def _check_probe(pid, read, bad, mode):
    rec = _P[pid]
    ticks, _extra, spans, title, (lo, hi) = read
    if "tlabel" in rec["cmd"] and ticks != rec["ticks"]:
        bad.append((mode, pid, "ticks", ticks, rec["ticks"]))
    if spans != rec["lines"]:
        bad.append((mode, pid, "lines", spans, rec["lines"]))
    if [title] != rec["title"]:
        bad.append((mode, pid, "title", title, rec["title"]))
    if lo > rec["range"][0] + 1e-6 or hi < rec["range"][1] - 1e-6:
        bad.append((mode, pid, "range", (lo, hi), rec["range"]))


@pytest.mark.parametrize("mode", MODES)
class TestTheFoldedSpecDrawsAsTwoway:
    def test_probe(self, tmp_path, mode):
        """Each probe's folded keys drawn give twoway's ticks, lines,
        title and a range holding twoway's (every probe checked)."""
        bad = []
        for pid, go in _FOLDED.items():
            _root, figs = _build(tmp_path, mode, [_TSLINE], go)
            assert len(figs) == 1, (pid, mode)
            _check_probe(pid, _read(figs[0]), bad, mode)
        assert not bad, bad


@pytest.mark.parametrize("mode", MODES)
class TestAfterAFilterMove:
    def test_probe(self, tmp_path, mode):
        """c01 + c05 + c07 folded, before and after a dropdown move."""
        root, figs = _build(tmp_path, mode, [_TSLINE], _ALL, filt="g")
        before = _read(figs[0])
        if mode == "saved":
            _move(root, ("Select", "1"))
        else:
            _served_move(root, "Select", "1")
        after = _read(figs[0])
        want = ([480, 492, 504, 516, 528], [504.0], "Month")
        assert (before[0], before[2], before[3]) == want
        assert (after[0], after[2], after[3]) == want


@pytest.mark.parametrize("mode", MODES)
class TestAMixedAxis:
    def test_layers(self, tmp_path, mode):
        """A %tm layer first beside a numeric or a %td one: the folded
        line and labels at 2002m1 and 2000m1 .. 2004m1 (Stata units)."""
        bad = []
        for other in ("n", "d"):
            plots = [_TSLINE, {"type": "line", "yvar": "z", "xvar": other,
                               "options": {}}]
            _r, figs = _build(tmp_path, mode, plots,
                              {"xline": "504", "xlabel": "480(12)528"})
            ticks, _e, spans, _t, _rg = _read(figs[0])
            if (ticks, spans) != ([480, 492, 504, 516, 528], [504.0]):
                bad.append((other, ticks, spans))
        assert not bad, bad


@pytest.mark.parametrize("mode", MODES)
class TestUnderBy:
    def test_each_panel(self, tmp_path, mode):
        """by(g): every panel draws the folded line and labels, before and
        after a move."""
        go = dict(_ALL, by="g")
        root, figs = _build(tmp_path, mode, [_TSLINE], go, filt="g")
        assert len(figs) == 2, mode
        want = ([480, 492, 504, 516, 528], [504.0])
        assert [(_read(f)[0], _read(f)[2]) for f in figs] == [want, want]
        if mode == "saved":
            _move(root, ("Select", "1"))
        else:
            _served_move(root, "Select", "1")
        assert [(_read(f)[0], _read(f)[2]) for f in figs] == [want, want]


class TestTheRecordsAreCurrent:
    def test_rows(self):
        d = json.load(open(os.path.join(_ROOT, "test", "fixtures",
                                        "rejected_options.json"),
                           encoding="utf-8"))
        bad = []
        for r in d["rejected_options"]:
            if r["option"] not in _T_OPTS:
                continue
            want = ("stored-and-named-WP-30-P1.6"
                    if r["option"] in ("tmlabel", "tmtick")
                    else "implemented-WP-30-P1.6")
            if (r["dash_rc"], r["disposition"]) != (0, want):
                bad.append((r["option"], r["dash_rc"], r["disposition"]))
            if any(p["dash_rc"] for p in r["probes"]):
                bad.append((r["option"], "nested probe"))
        for p in d["probes"]:
            if p["id"] in _T_OPTS and p["dash_rc"]:
                bad.append(("probe", p["id"], p["dash_rc"]))
        tally = {}
        for r in d["rejected_options"]:
            tally[r["disposition"]] = tally.get(r["disposition"], 0) + 1
        if d["summary"]["by_disposition"] != tally:
            bad.append(("by_disposition", d["summary"]["by_disposition"],
                        tally))
        fails = sum(1 for p in d["probes"] if p["dash_rc"])
        if d["summary"]["dash_failures"] != fails:
            bad.append(("dash_failures", d["summary"]["dash_failures"],
                        fails))
        assert not bad, bad


class TestTheHelp:
    def test_it_documents_the_t_options(self):
        hlp = _source("dash.sthlp")
        assert "{marker taxis}" in hlp
        grp = hlp[hlp.index("{marker taxis}"):]
        grp = grp[:grp.index("{marker", 5)]
        for opt in _T_OPTS:
            assert "{opt %s()}" % opt in grp, opt
        for word in ("tm()", "ts()", "lfit", "xline()", "xscale(log)",
                     "dash build"):
            assert word in grp, word
        # Flipped (WP-31 D1): the Unsupported entry "Minor ticks and minor
        # labels" named tmlabel() and tmtick(), which was wrong once they
        # are drawn; the axis options' "Minor ticks and labels" paragraph
        # says they are drawn as xmlabel() and xmtick().
        assert "Minor ticks and minor labels." not in hlp
        i = hlp.index("{ul:Minor ticks and labels.}")
        par = hlp[i:hlp.index("\n\n", i)]
        assert "{opt tmtick()}" in par and "{opt tmlabel()}" in par

    def test_it_documents_axis2_format_and_left_aligned(self):
        grp = _source("dash.sthlp")
        grp = grp[grp.index("{marker taxis}"):]
        grp = grp[:grp.index("{marker", 5)]
        for word in ("axis(2)", "{opt tlabel2()}", "{opt tline2()}",
                     "format()", "%-tm"):
            assert word in grp, word
