"""mlabtextstyle(textstyle): marker labels in the scheme's text box styles
(WP-30 P1.24, part 2).

The defect: dash.ado declared mlabtextstyle() and put it on the pending
list, so ``dash scatter y x, mlabel(lab) mlabtextstyle(heading)`` named the
option in its note and drew the labels in the marker-label default.

twoway folds mlabtextstyle() rightmost into the labels' textstyle, and
mlabsize()/mlabcolor() into its size and colour, so those win in either
order (twoway_yxview_parse.class:656-664).  Each of Stata's 37 shipped
style/textboxstyle-<name>.style files reads ``set size scheme <key>`` and
``set color scheme <key>``.  ``test/fixtures/mlabtextstyle_truth.json``
(scripts/extract_mlabtextstyle_truth.do) holds that table and, under
stcolor, s2color, economist and s1rcolor, the size and fill twoway draws
each series' labels at for every name and for the override, list and
unknown-name cases.  Sizes are compared as ratios to the same scheme's
default label size, within 1%.
"""

import json
import os
import re
import sys
import time
import warnings

import pandas as pd
import pytest
from bokeh.models import LabelSet

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from test_mode_parity import _spec as _mp_spec  # noqa: E402
import test_mlabvposition as _mv  # noqa: E402
from probe_groups import probe_params, representative  # noqa: E402

# WP-47 MS-15: the marker labels are Text glyph renderers; a reader of the
# LabelSets they were reads them as conftest.MarkerLabels, beside any
# other LabelSet.
from bokeh.models import LabelSet  # noqa: E402
from conftest import MarkerLabels, mlabel_sets  # noqa: E402
_MLS = (LabelSet, MarkerLabels)


def _mls_center(fig):
    return list(fig.center) + mlabel_sets(fig)


def _mls_select(doc):
    return list(doc.select({"type": LabelSet})) + mlabel_sets(doc)


def _mls_all(objs):
    objs = list(objs)
    return objs + mlabel_sets(objs)


_FIX = json.load(open(os.path.join(_HERE, "fixtures",
                                   "mlabtextstyle_truth.json"),
                      encoding="utf-8"))
_SCHEMES = ("stcolor", "s2color", "economist", "s1rcolor")
_T = dr.OptionTranslator
_ADO = open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8").read()
_MATA = open(os.path.join(_ROOT, "dash_parse.mata"), encoding="utf-8").read()
_HELP = open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8").read()


def _parser(scheme):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return dr.SchemeParser(scheme)


def _pt(css):
    css = getattr(css, "value", css)
    if isinstance(css, dict):
        css = css.get("value")
    return _T.css_to_pt(css)


def _col(c):
    c = getattr(c, "value", c)
    if isinstance(c, dict):
        c = c.get("value")
    return str(c).lower()


class TestTheFixture:
    def test_it_is_stamped(self):
        m = _FIX["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert m.get(k), k
        assert m["stata_version"].startswith("19.")
        assert sorted(_FIX["schemes"]) == sorted(_SCHEMES)
        assert len(m["table"]) == 37
        note = " ".join(_FIX["schemes"]["stcolor"]["nosuch"]["notes"])
        assert "named style nosuch not found in class textstyle" in note


class TestTheTable:
    def test_it_is_the_fixtures_table(self):
        want = {k: tuple(v) for k, v in _FIX["_meta"]["table"].items()
                if "#" not in k}
        assert dr.SchemeParser._TEXTBOX_STYLES == want

    def test_every_name_resolves(self):
        bad = []
        for sch in _SCHEMES:
            sp = _parser(sch)
            base = _pt(sp.default_mlabel_style(0)[2])
            tw = _FIX["schemes"][sch]
            for n in list(sp._TEXTBOX_STYLES) + ["p1", "p3", "p3barlabel",
                                                 "p3boxlabel"]:
                size, color = sp.textbox_style(n)
                want = tw[n]["Q"]["size"] / tw["DEF"]["Q"]["size"]
                got = _pt(size) / base
                if abs(got - want) > 0.01 * want \
                        or color.lower() != tw[n]["Q"]["fill"]:
                    bad.append((sch, n, got, want, color, tw[n]["Q"]["fill"]))
        assert not bad, bad

    def test_the_note_table_agrees(self):
        for n, row in dr.SchemeParser._NOTE_TEXTBOXES.items():
            assert dr.SchemeParser._TEXTBOX_STYLES[n] == row[:2], n

    def test_case_and_range_are_twoways(self):
        sp = _parser("s2color")
        t0 = time.perf_counter()
        for n in ("Heading", "p0", "p16", "p3x", "../heading", "x" * 10000,
                  None, 3):
            assert sp.textbox_style(n) is None, n
        assert time.perf_counter() - t0 < 0.1
        for sch in _SCHEMES:
            for n in ("UC_Heading", "p0", "p16", "nosuch"):
                assert _FIX["schemes"][sch][n]["notes"], (sch, n)

    def test_the_fallback_resolves_as_s2color(self):
        fb, s2 = dr.SchemeParser.fallback(), _parser("s2color")
        for n in list(dr.SchemeParser._TEXTBOX_STYLES) + ["p3", "p3barlabel"]:
            assert fb.textbox_style(n) == s2.textbox_style(n), n


# ---------------------------------------------------------------------------
# The labels, in both modes: one dashboard per scheme, one graph per probe,
# each probe's labels named by its own label variables.
# ---------------------------------------------------------------------------

def _probe_opts(cmd):
    """The plots dash.ado writes for a probe's command (two for a list)."""
    o = cmd.split(",", 1)[1]
    opts = dict(re.findall(r"(mlab\w+)\(([^)]*)\)", o))
    copies = re.findall(r"mlabtextstyle\(([^)]*)\)", o)
    if copies:
        opts["mlabtextstyle"] = copies[-1].strip('"')
    if "y y2 x" in cmd:
        styles = opts.get("mlabtextstyle", "").split()
        out = []
        for j in range(2):
            p = {k: v for k, v in opts.items() if k not in ("mlabel",
                                                             "mlabtextstyle")}
            if j < len(styles) and styles[j] != ".":
                p["mlabtextstyle"] = styles[j]
            out.append(p)
        return out
    opts.pop("mlabel", None)
    return [opts]


def _dashboard(sch):
    probes = sorted(_FIX["schemes"][sch])
    cols = {"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0, 6.0], "y2": [3.0, 5.0, 7.0]}
    graphs = []
    for i, pid in enumerate(probes):
        plots = []
        for j, o in enumerate(_probe_opts(_FIX["schemes"][sch][pid]["cmd"])):
            lab = f"l{i}_{j}"
            cols[lab] = [f"{'QS'[j]}{i}_{r}" for r in range(3)]
            plots.append(_mv._plot("scatter", dict(o, mlabel=lab),
                                   yvar=("y", "y2")[j]))
        graphs.append((f"g{i}", plots, {"scheme": sch}))
    df = pd.DataFrame(cols).astype({c: object for c in cols
                                    if c.startswith("l")})
    return probes, _mp_spec(graphs=graphs), df


def _drawn(mode, sch):
    probes, spec, df = _dashboard(sch)
    ms = (_mv._saved if mode == "saved" else _mv._served)(spec, df)
    out = {}
    for ls in _mls_all(ms):
        if not isinstance(ls, _MLS):
            continue
        first = str(ls.source.data[_mv._field(ls.text)][0])
        m = re.match(r"([QS])([0-9]+)_", first)
        if m:
            out[(probes[int(m.group(2))], m.group(1))] = (
                _pt(ls.text_font_size), _col(ls.text_color))
    return out


_CACHE = {}


def _labels(mode, sch):
    if (mode, sch) not in _CACHE:
        _CACHE[(mode, sch)] = _drawn(mode, sch)
    return _CACHE[(mode, sch)]


#: One scheme per node (one build each), and the gate's served subset
#: (pytest speed, 22oct2026): stcolor and s2color (the defaults), then
#: every second scheme of the rest; release checks every scheme served.
_STYLE_PARAMS = probe_params(_SCHEMES, representative(
    _SCHEMES, always=("stcolor", "s2color"), stride=2), size=1)


class TestTheLabels:
    @pytest.mark.parametrize("mode,group", _STYLE_PARAMS)
    def test_style(self, mode, group):
        bad = []
        for sch in group:
            got = _labels(mode, sch)
            tw = _FIX["schemes"][sch]
            base = got[("DEF", "Q")][0]
            for pid, rec in tw.items():
                for ser in ("Q", "S"):
                    if ser not in rec:
                        continue
                    want = rec[ser]["size"] / tw["DEF"]["Q"]["size"]
                    g = got.get((pid, ser))
                    if g is None or abs(g[0] / base - want) > 0.01 * want \
                            or g[1] != rec[ser]["fill"]:
                        bad.append((sch, pid, ser, g, want, rec[ser]["fill"]))
        assert not bad, bad

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_an_unknown_name_is_noted_and_drawn_body(self, mode):
        from bokeh.document import Document
        from conftest import load_app, render_models
        dr._DASH_NOTED.clear()
        spec = _mp_spec([_mv._plot("scatter", {"mlabel": "lab",
                                               "mlabtextstyle": "Heading"})],
                        {"scheme": "stcolor"})
        tag, sp, dp = _mv._write(spec, _mv._DATA)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            if mode == "saved":
                ms = list(render_models(dr.DashRenderer(sp, dp))
                          ._last_layout_root.references())
            else:
                ap = os.path.join(_mv._TMP, f"app_ts_{tag}.py")
                dr.ServerAppBuilder(sp, dp).build(ap)
                doc = Document()
                load_app(ap, f"_mlabts_{tag}", draw=False).make_document(doc)
                ms = [m for r in doc.roots for m in r.references()]
        body = _parser("stcolor").textbox_style("body")
        drawn = {(_pt(ls.text_font_size), _col(ls.text_color))
                 for ls in _mls_all(ms) if isinstance(ls, _MLS)}
        assert drawn == {(_pt(body[0]), body[1].lower())}, drawn
        msgs = [str(w.message) for w in caught]
        assert ("dash: mlabtextstyle(Heading) is not a recognised text "
                "style; using the body text style.") in msgs, msgs


class TestTheSpecCarriesIt:
    def test_the_parser_writes_one_element_per_series(self):
        body = _mv._program(_ADO, "_dash_parse_plot_opts")
        assert "MLABTextstyle(string asis)" in body
        assert re.search(r"sreturn local mlabtextstyle\s+: copy local "
                         r"mlabtextstyle", body)
        assert "_dash_pending' mlabtextstyle" not in body
        assert re.search(r"\bmlabtextstyle\b",
                         _mv._program(_ADO, "_dash_plot_opts_to_json"))
        m = re.search(r"string scalar _dash_stylelist_keys\(\)\s*\{(.*?)\}",
                      _MATA, re.S)
        assert m and "mlabtextstyle" in m.group(1)
        assert "mlabtextstyle" not in _mv._ALLOW


class TestTheSchemeFiles:
    def test_every_scheme_carries_the_textbox_keys(self):
        truth = json.load(open(os.path.join(_HERE, "fixtures",
                                            "scheme_truth.json")))
        bad = []
        for sch, e in truth.items():
            if sch == "_meta" or not isinstance(e, dict):
                continue
            path = os.path.join(_ROOT, f"dash-{sch}.scheme")
            if not os.path.exists(path):
                continue
            text = open(path, encoding="utf-8").read()
            for key, v in e.items():
                m = re.fullmatch(r"textbox_(\w+)_(size|color)", key)
                if not m or v is None:
                    continue
                cls = "gsize" if m.group(2) == "size" else "color"
                if not re.search(rf"^{cls}\s+{m.group(1)}\s", text, re.M):
                    bad.append((sch, cls, m.group(1)))
        assert not bad, bad


class TestTheHelp:
    def test_the_help_documents_it(self):
        assert "{cmdab:mlabt:extstyle(}" in _HELP
        assert "{ul:Marker-label text style.}" not in _HELP
