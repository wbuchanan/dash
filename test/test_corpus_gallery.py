"""
test_corpus_gallery.py -- the corpus's publication layer (WP-33 33-08).

scripts/corpus/gallery.py turns a corpus run into docs/gallery/ (the SVG
pairs, corpus.json, one dash-built page per plot type and a dash-built index
page) and README.md's gallery block; scripts/corpus/summary.py counts a run
for `make corpus'.  Every function is tested here on a fake run of three
examples, with no Stata and no Chrome: page.do files are read as text, the
Stata slot is a small Python stand-in and the Chrome probe a stub.  The
gallery is built only at WP-50's closeout (DECISIONS P4-8); the two
TestTheCommittedGallery tests bind then and assert today that nothing is
committed.
"""
import base64
import json
import os
import re
import subprocess
import sys
import time

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from scripts.corpus import gallery, ledger, summary, twoway_run  # noqa: E402

#: Where GitHub Pages serves docs/gallery (.github/workflows/pages.yml), the
#: link make gallery writes into README.md's block.
_GALLERY_URL = "https://wbuchanan.github.io/dash/gallery/"

_TW_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="60">'
           '<clipPath id="r9"><rect width="5" height="5"/></clipPath>'
           '<path clip-path="url(#r9)" d="M0 0L10 10"/></svg>')
_DA_SVG = '<svg xmlns="http://www.w3.org/2000/svg"><path id="d1" d="M1 1L2 2"/></svg>'
_PNG_IMAGE = '<image href="data:image/png;base64,iVBORw0KGgo=" width="4" height="4"/>'

_IDS = ("help-scatter-aaaa0001", "help-scatter-bbbb0002", "audit-line-cccc0003")


def _example(i, plottype="scatter", setup=("sysuse auto, clear",), cmd=None, source="help",
             duplicates=()):
    cmd = cmd or "scatter mpg weight"
    return {"id": i, "source": source, "sources": [source], "file": "scatter.sthlp",
            "line": 10, "entry": "1", "finding": None, "setup": list(setup), "cmd": cmd,
            "dash_cmd": "dash " + cmd, "plottype": plottype, "datasets": [],
            "stripped": [], "signature": plottype, "duplicates": list(duplicates)}


def _verdict(i, plottype="scatter", rc_tw=0, rc_da=0, verdict="Same", summary_="Same",
             gallery_=True, checks=(), ledger_=(), source="help", first_dash=None,
             size_matched=True):
    diffs = [{"check": c, "twoway": 1, "dash": 2, "within_tol": False,
              "gaps4": (ledger_[0] if ledger_ else None)} for c in checks]
    return {"id": i, "plottype": plottype, "source": source, "rc_twoway": rc_tw,
            "rc_dash": rc_da, "rc_pair": [rc_tw, rc_da], "first_twoway": None,
            "first_dash": first_dash, "verdict": verdict, "ssim": 0.95,
            "size_matched": size_matched, "panels": "1 of 1", "differences": diffs,
            "checks": sorted(checks), "ledger": sorted(ledger_), "summary": summary_,
            "colours": {"twoway": [], "dash": [], "unread": 0}, "gallery": gallery_,
            "skip": None}


def _row(i, plottype="scatter", setup=("sysuse auto, clear",), cmd=None, rc_da=0,
         dash_svg=True, **kw):
    """One joined row (load_run's shape) built in memory."""
    return {"id": i, "example": _example(i, plottype, setup, cmd),
            "twoway": {"id": i, "rc": kw.get("rc_tw", 0), "svg": "twoway/%s.svg" % i},
            "dash": {"id": i, "rc": rc_da, "svg": ("dash/%s.svg" % i) if dash_svg else None,
                     "first_line": kw.get("first_dash")},
            "verdict": _verdict(i, plottype, rc_da=rc_da, **kw)}


def _write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _fake_run(tmp_path, extra_dash_svg=None):
    """A run of three examples: two scatter rows from two setups (the first
    Close with a GAPS4 id behind it), and one example twoway refuses."""
    run = tmp_path / "run"
    (run / "twoway").mkdir(parents=True)
    (run / "dash").mkdir()
    a, b, c = _IDS
    ex = [_example(a, duplicates=["gpdf-scatter-dddd0004"]),
          _example(b, setup=["sysuse lifeexp, clear"], cmd="scatter lexp gnppc"),
          _example(c, plottype="line", source="audit", cmd="line y x, bogus")]
    tw = [{"id": a, "rc": 0, "first_line": None, "setup_rc": 0, "export_rc": 0,
           "svg": "twoway/%s.svg" % a, "width_in": 7.5, "height_in": 4.5, "skip": None},
          {"id": b, "rc": 0, "first_line": None, "setup_rc": 0, "export_rc": 0,
           "svg": "twoway/%s.svg" % b, "width_in": 7.5, "height_in": 4.5, "skip": None},
          {"id": c, "rc": 198, "first_line": "option bogus not allowed", "setup_rc": 0,
           "export_rc": None, "svg": None, "width_in": None, "height_in": None,
           "skip": None}]
    da = [{"id": a, "rc": 0, "first_line": None, "setup_rc": 0, "html": "dash/%s.html" % a,
           "skip": None, "svg": "dash/%s.svg" % a, "view": "dash/%s.view.json" % a,
           "size_matched": True, "js_errors": [], "w": 720, "h": 432, "export_error": None},
          {"id": b, "rc": 0, "first_line": None, "setup_rc": 0, "html": "dash/%s.html" % b,
           "skip": None, "svg": "dash/%s.svg" % b, "view": "dash/%s.view.json" % b,
           "size_matched": False, "js_errors": [], "w": 720, "h": 432, "export_error": None},
          {"id": c, "rc": 198, "first_line": "option bogus not allowed", "setup_rc": 0,
           "html": None, "skip": None, "svg": None, "view": None, "size_matched": None,
           "js_errors": None, "w": None, "h": None, "export_error": None}]
    ve = [_verdict(a, verdict="Close", summary_="x-axis ticks, legend keys",
                   checks=("legend", "x_ticks"), ledger_=("AX-4",)),
          _verdict(b, size_matched=False),
          _verdict(c, plottype="line", rc_tw=198, rc_da=198, verdict="Same",
                   gallery_=False, source="audit", first_dash="option bogus not allowed",
                   size_matched=None)]
    _write_jsonl(run / "examples.jsonl", ex)
    _write_jsonl(run / "twoway.jsonl", tw)
    _write_jsonl(run / "dash.jsonl", da)
    _write_jsonl(run / "verdicts.jsonl", ve)
    for i in (a, b):
        (run / "twoway" / ("%s.svg" % i)).write_text(_TW_SVG, encoding="utf-8")
        (run / "dash" / ("%s.svg" % i)).write_text(extra_dash_svg or _DA_SVG,
                                                   encoding="utf-8")
    (run / "stata_version.txt").write_text("19.5\n", encoding="utf-8")
    (run / "extract_duplicates.tsv").write_text(
        "dropped_id\tkept_id\tsource\tcmd\ngpdf-scatter-dddd0004\t%s\tgpdf\tscatter mpg weight\n"
        % a, encoding="utf-8")
    return run


@pytest.fixture
def cache(tmp_path, monkeypatch):
    d = tmp_path / "cache"
    d.mkdir()
    monkeypatch.setenv("DASH_CORPUS_CACHE", str(d))
    return str(d)


def _fake_slot(tmp_path, log_by_dir, calls=None):
    """A stand-in for stata_slot.sh: writes <page_dir>/page.log from log_by_dir
    (keyed by the page folder's name, "*" for any other) and records each call."""
    script = tmp_path / "fake_slot.py"
    script.write_text(
        "import json, os, sys\n"
        "d = sys.argv[1]\n"
        "logs = json.loads(%r)\n"
        "calls = %r\n"
        "if calls:\n"
        "    open(calls, 'a').write(os.path.basename(d) + '\\n')\n"
        "text = logs.get(os.path.basename(d), logs.get('*'))\n"
        "if text is not None:\n"
        "    open(os.path.join(d, 'page.log'), 'w').write(text)\n"
        % (json.dumps(log_by_dir), str(calls) if calls else ""), encoding="utf-8")
    return [sys.executable, str(script)]


def _tree(path):
    out = {}
    for base, _dirs, files in os.walk(path):
        for f in files:
            p = os.path.join(base, f)
            with open(p, "rb") as fh:
                out[os.path.relpath(p, path)] = (fh.read(), os.path.getmtime(p))
    return out


class TestLoadRun:

    def test_joins_by_id_and_counts_drops(self, tmp_path):
        run = _fake_run(tmp_path)
        with open(run / "dash.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": "help-scatter-zzzz9999", "rc": 0}) + "\n")
        rows, missing = gallery.load_run(str(run))
        # D52: the example twoway refuses is dropped, neither a row nor missing.
        assert [r["id"] for r in rows] == sorted(_IDS[:2])
        assert missing == ["help-scatter-zzzz9999"]
        r = {r["id"]: r for r in rows}[_IDS[0]]
        assert set(r) == {"id", "example", "twoway", "dash", "verdict"}
        assert r["verdict"]["summary"] == "x-axis ticks, legend keys"
        assert r["example"]["duplicates"] == ["gpdf-scatter-dddd0004"]


class TestWithName:

    def test_comma_rules(self):
        assert gallery.with_name("dash scatter y x", "g1") == "dash scatter y x, name(g1)"
        assert (gallery.with_name("dash scatter y x, mc(red)", "g2")
                == "dash scatter y x, mc(red) name(g2)")
        assert (gallery.with_name("dash (scatter y x, mc(red)) (line y x)", "g3")
                == "dash (scatter y x, mc(red)) (line y x), name(g3)")


class TestPages:

    def test_only_what_twoway_draws_by_type_in_id_order(self):
        rows = [_row("b-2"), _row("a-1", plottype="line"), _row("c-3"),
                _row("d-4", rc_tw=198, gallery_=False), _row("e-5", gallery_=False)]
        p = gallery.pages(rows)
        assert list(p) == ["line", "scatter"]
        assert [r["id"] for r in p["scatter"]] == ["b-2", "c-3"]
        assert [r["id"] for r in p["line"]] == ["a-1"]
        with pytest.raises(ValueError, match="f-6"):
            gallery.pages([_row("f-6", plottype="Scatter")])

    def test_on_gallery_is_drawn_by_twoway_and_not_left_out(self):
        assert gallery.on_gallery(_row("a-1"))
        assert not gallery.on_gallery(_row("b-2", gallery_=False))
        assert not gallery.on_gallery(_row("c-3", plottype="contour"))

    def test_a_left_out_plot_type_gets_no_page(self):
        """D78: contour's page held 107 MB, over GitHub's 100 MB file limit."""
        assert gallery.LEFT_OUT == ("contour",)
        p = gallery.pages([_row("a-1", plottype="contour"), _row("b-2")])
        assert list(p) == ["scatter"]


class TestCopySvgs:

    def test_copies_and_normalises_into_the_stage(self, tmp_path):
        run = _fake_run(tmp_path)
        rows, _ = gallery.load_run(str(run))
        out = tmp_path / "out"
        got = gallery.copy_svgs(rows, str(run), str(out))
        a, b, c = _IDS
        assert got[a] == {"twoway_svg": "svg/%s-twoway.svg" % a,
                          "dash_svg": "svg/%s-dash.svg" % a}
        assert c not in got
        assert sorted(os.listdir(out)) == ["svg"]
        assert sorted(os.listdir(out / "svg")) == sorted(
            ["%s-twoway.svg" % a, "%s-dash.svg" % a, "%s-twoway.svg" % b, "%s-dash.svg" % b])
        tw = (out / "svg" / ("%s-twoway.svg" % a)).read_text(encoding="utf-8")
        assert 'id="d1"' in tw and "url(#d1)" in tw and "r9" not in tw
        assert (out / "svg" / ("%s-dash.svg" % a)).read_text(encoding="utf-8") == _DA_SVG

    def test_no_svgs_for_a_left_out_plot_type(self, tmp_path):
        run = _fake_run(tmp_path)
        rows, _ = gallery.load_run(str(run))
        a, b, _c = _IDS
        {r["id"]: r for r in rows}[a]["example"]["plottype"] = "contour"
        out = tmp_path / "out"
        got = gallery.copy_svgs(rows, str(run), str(out))
        assert a not in got and b in got
        assert sorted(os.listdir(out / "svg")) == sorted(
            ["%s-twoway.svg" % b, "%s-dash.svg" % b])


class TestSetupFrames:

    def test_shared_by_identical_setups_and_read_from_the_cache(self, cache):
        rows = [_row("a-1"), _row("b-2"), _row("c-3", setup=["webuse lbw, clear"]),
                _row("d-4", setup=["sysuse lifeexp, clear"])]
        frames, missing = gallery.setup_frames(rows, cache)
        assert frames == {"sysuse auto, clear": "gf1",
                          'use "%s/lbw.dta", clear' % cache: "gf2",
                          "sysuse lifeexp, clear": "gf3"}
        assert missing == {"gf1": [], "gf2": ["lbw"], "gf3": []}


class TestCaptions:

    def test_the_twoway_image_has_no_caption_and_no_verdict(self):
        """The command is the panel's (panel_texts), not the picture's: the
        twoway image has no caption, so no verdict is drawn on a page."""
        for r in (_row("a-1", verdict="Differs", summary_="marker symbol"),
                  _row("b-2", verdict="Same"),
                  _row("c-3", rc_da=198, first_dash="option foo not allowed",
                       verdict="Differs", summary_="return code"),
                  _row("e-5", verdict="Close", summary_="x-axis ticks (AX-4)")):
            cap, alt = gallery.captions(r, "twoway")
            assert cap == "" and alt == "twoway: scatter mpg weight", r["id"]
        long_cmd = "scatter mpg weight, title(" + "x" * 600 + ")\r\nnote(y)"
        cap, alt = gallery.captions(_row("d-4", cmd=long_cmd), "twoway")
        assert cap == "" and "\r" not in alt and "\n" not in alt
        assert len(alt) == 200 and alt.endswith("...")

    def test_stata_terms_only(self):
        for bad in ("x ticks (AX-4)", "plot:PT-13", "glyph_extents", "frame gf2"):
            assert gallery.stata_terms_only(bad) is False, bad
        assert gallery.stata_terms_only("x-axis ticks, legend keys") is True


class TestPanelTexts:

    def test_label_command_and_a_refusals_note(self):
        r = _row("a-1", verdict="Close", summary_="x-axis ticks, legend keys")
        assert gallery.panel_texts(r, "twoway", "live") == (
            "Stata on twoway", "scatter mpg weight", "")
        assert gallery.panel_texts(r, "dash", "live") == (
            "Stata on dash", "dash scatter mpg weight", "")
        assert gallery.panel_texts(r, "dash", "static")[2] == ""
        r = _row("c-3", rc_da=198, first_dash="option foo not allowed")
        assert gallery.panel_texts(r, "dash", "refused") == (
            "Stata on dash", "dash scatter mpg weight",
            "dash r(198): option foo not allowed")
        # A graph the corpus drew but the page's own session refused.
        assert gallery.panel_texts(_row("d-4"), "dash", "refused")[2] == (
            "dash did not draw this graph on this page")
        long_cmd = "scatter mpg weight, title(" + "x" * 600 + ")\r\nnote(y)"
        label, cmd, _ = gallery.panel_texts(_row("e-5", cmd=long_cmd), "dash", "live")
        assert cmd.startswith("dash scatter") and len(cmd) == 400 and cmd.endswith("...")
        assert "\r" not in cmd and "\n" not in cmd
        with pytest.raises(ValueError):
            gallery.panel_texts(r, "stata", "live")


# ---- a page as the gallery's page.do builds it ---------------------------------

_SMOKE = os.path.join(_ROOT, "test", "fixtures", "svg_truth_smoke.svg")
_PANEL_ROWS = (("a-1", "scatter mpg weight", "live"),
               ("b-2", 'scatter mpg weight, title("<b>&")', "refused"),
               ("c-3", "scatter mpg weight, msymbol(oh)", "static"))


def _panel_rows():
    rows = [_row(i, cmd=c, rc_da=(198 if k == "refused" else 0),
                 first_dash=("option foo not allowed" if k == "refused" else None))
            for i, c, k in _PANEL_ROWS]
    return rows, {i: k for i, _c, k in _PANEL_ROWS}


def gallery_page_html(rows, kinds):
    """The page dash build writes for the gallery's layout: row k's twoway
    image t<k> at (k,1) beside its dash graph g<k> (a static dash image d<k>,
    nothing for a refused row) at (k,2)."""
    import warnings
    import numpy as np
    import pandas as pd
    from bokeh.io import curdoc
    sys.path.insert(0, os.path.join(_ROOT, "test"))
    import dash_render as dr
    from conftest import make_data_json
    graphs, images, lay = [], [], []
    for k, r in enumerate(rows, 1):
        images.append({"name": "t%d" % k, "path": _SMOKE, "caption": "",
                       "alt": gallery.captions(r, "twoway")[1], "link": ""})
        lay.append("t%d:%d,1" % (k, k))
        kind = kinds[r["id"]]
        if kind == "live":
            graphs.append({"name": "g%d" % k,
                           "graph_options": {"name": "g%d" % k, "scheme": "stcolor"},
                           "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                                      "options": {}}], "if_expr": "", "in_expr": ""})
            lay.append("g%d:%d,2" % (k, k))
        elif kind == "static":
            images.append({"name": "d%d" % k, "path": _SMOKE, "caption": "",
                           "alt": "dash: " + r["example"]["cmd"], "link": ""})
            lay.append("d%d:%d,2" % (k, k))
    spec = {"graphs": graphs, "kpis": [], "images": images,
            "build_options": {"layout": " ".join(lay), "link": "", "theme": "",
                              "title": "dash beside twoway: scatter", "subtitle": "",
                              "filter": "", "tabs": "",
                              "registry": " ".join(c.split(":")[0] for c in lay)}}
    i = np.arange(12, dtype=float)
    frame = pd.DataFrame({"mpg": 12.0 + i, "weight": 2000.0 + 100.0 * i})
    import tempfile
    with tempfile.TemporaryDirectory(prefix="dash_gallery_page_") as tmp:
        sp, dp = os.path.join(tmp, "spec.json"), os.path.join(tmp, "data.json")
        with open(sp, "w") as fh:
            json.dump(spec, fh)
        with open(dp, "w") as fh:
            json.dump(make_data_json(frame), fh)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                return dr.DashRenderer(sp, dp).render()
            finally:
                curdoc().clear()


@pytest.fixture(scope="module")
def built_page():
    rows, kinds = _panel_rows()
    return gallery_page_html(rows, kinds)


def _doc_json(text):
    import html as _html
    m = re.search(r'<script type="application/json" id="[^"]+">(.*?)</script>', text, re.S)
    return json.loads(_html.unescape(m.group(1))), m


def _grid(doc):
    root = list(doc.values())[0]["roots"][0]
    return [c for c in root["attributes"]["children"] if c.get("name") == "GridPlot"][0]


def _styles(model):
    return dict(model["attributes"]["styles"]["entries"])


class TestPanelPage:

    def test_each_cell_is_labelled_above_and_commanded_below(self, tmp_path, built_page):
        rows, kinds = _panel_rows()
        path = tmp_path / "scatter.html"
        path.write_text(built_page, encoding="utf-8")
        before = {(c[1], c[2]): c[0]["id"] for c in _grid(_doc_json(built_page)[0])
                  ["attributes"]["children"]}
        assert gallery.panel_page(str(path), rows, kinds) == 6
        doc, _ = _doc_json(path.read_text(encoding="utf-8"))
        cells = {(c[1], c[2]): c[0] for c in _grid(doc)["attributes"]["children"]}
        assert sorted(cells) == [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]
        for (r, c), panel in cells.items():
            side = ("twoway", "dash")[c]
            row = rows[r]
            assert panel["name"] == "Column", panel["name"]
            assert panel["attributes"]["name"] == "gallery-panel-" + side
            kids = panel["attributes"]["children"]
            assert len(kids) == 3, kids
            label, cmd, note = gallery.panel_texts(row, side, kinds[row["id"]])
            assert kids[0]["name"] == "Div" and label in kids[0]["attributes"]["text"]
            assert kids[-1]["name"] == "Div"
            text = kids[-1]["attributes"]["text"]
            assert "<code" in text and gallery.html.escape(cmd) in text, text
            if (r, c) in before:
                assert kids[1]["id"] == before[(r, c)]
            else:  # the refused row's dash side: its note in place of a graph
                assert (r, c) == (1, 1) and gallery.html.escape(note) in \
                    kids[1]["attributes"]["text"]
        assert "<b>&" not in path.read_text(encoding="utf-8")
        tw, da = _styles(cells[(0, 0)]), _styles(cells[(0, 1)])
        assert tw["padding"] == da["padding"] and tw["box-sizing"] == "border-box"
        assert tw["border"].split()[:2] == da["border"].split()[:2]
        assert tw["background-color"] != da["background-color"]
        # Both are coloured frames round the picture: twoway's orange, dash's blue.
        assert tw["background-color"] == "#fdeedf" and tw["border"] == "1px solid #eda25c"
        assert da["background-color"] == "#e8f1fb" and da["border"] == "1px solid #7fb0e0"

    def test_only_the_layout_changes_and_twice_is_once(self, tmp_path, built_page):
        rows, kinds = _panel_rows()
        path = tmp_path / "scatter.html"
        path.write_text(built_page, encoding="utf-8")
        gallery.panel_page(str(path), rows, kinds)
        after = path.read_text(encoding="utf-8")
        _, m0 = _doc_json(built_page)
        _, m1 = _doc_json(after)
        assert built_page[:m0.start(1)] == after[:m1.start(1)]
        assert built_page[m0.end(1):] == after[m1.end(1):]
        assert gallery.panel_page(str(path), rows, kinds) == 0
        assert path.read_text(encoding="utf-8") == after

    def test_a_long_command_is_known_by_dashs_shortened_name(self, tmp_path):
        """dash names a picture by its alt() cut to 120 characters
        (_dash_aria); a row whose command is longer is still its row (the
        gallery's scatter page stopped at its row 17)."""
        cmd = ('scatter mpg weight, mc(navy) ms(circle) msi(medium) title("Fuel '
               'Efficiency vs. Weight") xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")')
        rows = [_row("a-1", cmd=cmd)]
        kinds = {"a-1": "live"}
        path = tmp_path / "scatter.html"
        path.write_text(gallery_page_html(rows, kinds), encoding="utf-8")
        assert len(gallery.captions(rows[0], "twoway")[1]) > 120
        assert gallery.panel_page(str(path), rows, kinds) == 2
        doc, _ = _doc_json(path.read_text(encoding="utf-8"))
        cells = {(c[1], c[2]): c[0] for c in _grid(doc)["attributes"]["children"]}
        assert gallery.html.escape(cmd) in \
            cells[(0, 0)]["attributes"]["children"][-1]["attributes"]["text"]

    def test_a_page_unlike_its_rows_is_refused_and_kept(self, tmp_path, built_page):
        rows, kinds = _panel_rows()
        path = tmp_path / "scatter.html"
        path.write_text(built_page, encoding="utf-8")
        for bad_rows, bad_kinds in ((rows[:2], kinds),
                                    ([rows[1], rows[0], rows[2]], kinds),
                                    (rows, dict(kinds, **{"a-1": "refused"}))):
            with pytest.raises(ValueError, match="scatter.html"):
                gallery.panel_page(str(path), bad_rows, bad_kinds)
            assert path.read_text(encoding="utf-8") == built_page
        path.write_text("<html></html>", encoding="utf-8")
        with pytest.raises(ValueError, match="scatter.html"):
            gallery.panel_page(str(path), rows, kinds)


def _page_do(tmp_path, rows, page="scatter"):
    out = tmp_path / "out"
    pdir = tmp_path / "run" / "gallery" / page
    path, kinds = gallery.write_page(page, rows, str(out), str(pdir), "/repo")
    with open(path, encoding="utf-8") as fh:
        return fh.read(), kinds, pdir, out


class TestWritePage:

    def test_caps_frames_prefix_and_placement(self, tmp_path, cache):
        rows = [_row("a-1"), _row("b-2", rc_da=198, first_dash="r198 text"),
                _row("c-3", setup=["sysuse lifeexp, clear"], cmd="scatter lexp gnppc")]
        do, kinds, pdir, out = _page_do(tmp_path, rows)
        assert kinds == {"a-1": "live", "b-2": "refused", "c-3": "live"}
        assert "global dash_max_graphs 1000" in do and "global dash_max_images 1000" in do
        assert "dash_max_bytes" not in do and "dash_max_cells" not in do
        assert 'adopath ++ "/repo/"' in do and "global dash_nobrowser 1" in do
        assert "frame gf1: capture noisily dash scatter mpg weight, name(g1)" in do
        assert "frame gf2: capture noisily dash scatter lexp gnppc, name(g3)" in do
        assert "frame(" not in do and "frame drop" not in do
        assert 'frame gf1: capture noisily do "%s/setup_1.do"' % pdir in do
        assert (pdir / "setup_1.do").read_text(encoding="utf-8") == "sysuse auto, clear\n"
        for cell in ("t1:1,1", "g1:1,2", "t2:2,1", "t3:3,1", "g3:3,2"):
            assert cell in do, cell
        assert "g2:" not in do
        for m in re.finditer(r'dash image using "([^"]+)"', do):
            assert m.group(1).startswith(str(out) + "/svg/"), m.group(1)
        assert 'saving("%s/scatter.html")' % out in do
        # The page is drawn in the session's scheme, as each twoway example
        # was: without it, one example's scheme() (scatter-3's economist)
        # was every other graph's on the page (_resolve_scheme_name).
        build = [ln for ln in do.splitlines() if "dash build," in ln]
        assert len(build) == 1 and "scheme(`c(scheme)')" in build[0], build
        assert do.count("##GRAPH") == 2 and do.count("##IMAGE") == 3
        assert do.rstrip().endswith('display "##BUILD " _rc')

    def test_captions_are_read_not_typed(self, tmp_path, cache):
        cmd = 'scatter mpg weight, title("a `b\' $x")'
        do, _, pdir, _ = _page_do(tmp_path, [_row("a-1", cmd=cmd)])
        caps = (pdir / "captions.txt").read_text(encoding="utf-8")
        assert cmd in caps
        for ln in do.splitlines():
            if "caption(" in ln:
                assert "$x" not in ln and "title(" not in ln, ln
                assert "caption(`\"`macval(cap)'\"')" in ln

    def test_a_missing_dataset_goes_static(self, tmp_path, cache):
        rows = [_row("a-1"), _row("b-2", setup=["webuse lbw, clear"])]
        do, kinds, pdir, _ = _page_do(tmp_path, rows)
        assert kinds == {"a-1": "live", "b-2": "static"}
        assert do.count("frame create") == 1 and "frame create gf1" in do
        assert "lbw" not in do.split("file open")[0]
        assert "name(d2)" in do and "d2:2,2" in do and "##STATIC b-2" in do
        caps = (pdir / "captions.txt").read_text(encoding="utf-8").splitlines()
        assert "dash's exported SVG (static: dataset not in the cache: lbw)" in caps
        assert "dash: scatter mpg weight" in caps

    def test_ts_operators_sort_and_weights_stay_live(self, tmp_path, cache):
        rows = [_row("a-1", plottype="line", cmd="line L.close date"),
                _row("b-2", plottype="line", cmd="line close date, sort(date)"),
                _row("c-3", plottype="line", cmd="scatter y x [aw=pop/1000]")]
        _, kinds, _, _ = _page_do(tmp_path, rows, page="line")
        assert set(kinds.values()) == {"live"}

    def test_setups_holding_a_variable_differently_stay_live(self, tmp_path, cache):
        rows = [_row("a-1"),
                _row("b-2", setup=["sysuse auto, clear",
                                   'label define origin 0 "US" 1 "Abroad", replace'])]
        do, kinds, _, _ = _page_do(tmp_path, rows)
        assert kinds == {"a-1": "live", "b-2": "live"}
        assert "frame create gf1" in do and "frame create gf2" in do


class TestPageParts:

    def test_parts_hold_the_counts_and_keep_rows_live(self, cache):
        rows = [_row("r-%d" % k, setup=["sysuse s%d, clear" % k]) for k in range(1, 6)]
        parts = gallery.page_parts("scatter", rows, cache, frame_limit=5)
        assert [p for p, _ in parts] == ["scatter", "scatter-2"]
        assert [r["id"] for r in parts[0][1]] == ["r-1", "r-2", "r-3"]
        assert [r["id"] for r in parts[1][1]] == ["r-4", "r-5"]
        many = [_row("m-%04d" % k) for k in range(501)]
        parts = gallery.page_parts("scatter", many, cache, frame_limit=None)
        assert [(p, len(rs)) for p, rs in parts] == [("scatter", 500), ("scatter-2", 1)]
        parts = gallery.page_parts("scatter", rows[:3], cache, frame_limit=None)
        assert [p for p, _ in parts] == ["scatter"]
        mixed = [rows[0], rows[1], _row("w-1", setup=["webuse nosuch, clear"]), rows[2]]
        parts = gallery.page_parts("scatter", mixed, cache, frame_limit=5)
        assert [p for p, _ in parts] == ["scatter"] and len(parts[0][1]) == 4


def _ids(page_rows):
    return {p: [r["id"] for r in rows] for p, rows in page_rows.items()}


class TestResplit:
    """D78: a plot type with a built page over the byte cap is split again."""

    def test_pages_within_the_cap_stay(self, cache):
        page_rows = {"line": [_row("l-1", plottype="line")], "scatter": [_row("s-1")]}
        got, redo = gallery.resplit(page_rows, {"line": 200, "scatter": 900}, cache, cap=1000)
        assert redo == set() and _ids(got) == _ids(page_rows)

    def test_an_over_cap_type_is_split_by_its_bytes_a_row(self, cache):
        # base 200 (the smallest page), 100 bytes a row; 0.9 * cap - base = 700.
        rows = [_row("s-%02d" % k) for k in range(10)]
        page_rows = {"line": [_row("l-1", plottype="line")], "scatter": rows}
        got, redo = gallery.resplit(page_rows, {"line": 200, "scatter": 1200}, cache,
                                    cap=1000)
        assert redo == {"scatter"}
        assert list(got) == ["line", "scatter", "scatter-2"]
        assert _ids(got)["scatter"] == ["s-%02d" % k for k in range(7)]
        assert _ids(got)["scatter-2"] == ["s-07", "s-08", "s-09"]
        assert got["line"] is page_rows["line"]

    def test_parts_are_joined_and_renumbered_in_order(self, cache):
        page_rows = {"scatter": [_row("s-%02d" % k) for k in range(4)],
                     "scatter-2": [_row("s-%02d" % k) for k in range(4, 8)],
                     "zline": [_row("z-1", plottype="line")]}
        sizes = {"scatter": 600, "scatter-2": 1400, "zline": 200}
        got, redo = gallery.resplit(page_rows, sizes, cache, cap=1000)
        assert redo == {"scatter"} and list(got)[-1] == "zline"
        flat = [i for p in got if p != "zline" for i in _ids(got)[p]]
        assert flat == ["s-%02d" % k for k in range(8)]
        assert [p for p in got if p != "zline"] == [
            "scatter"] + ["scatter-%d" % k for k in range(2, len(got))]
        assert len(got) - 1 > 2

    def test_a_lone_page_is_split_and_frames_still_bound_a_part(self, cache):
        # One page: the base is at most a quarter of the cap, so it splits.
        rows = [_row("r-%d" % k, setup=["sysuse s%d, clear" % k]) for k in range(1, 7)]
        got, redo = gallery.resplit({"scatter": rows}, {"scatter": 2000}, cache, cap=1000,
                                    frame_limit=4)
        assert redo == {"scatter"}
        assert all(len(rs) <= 2 for rs in got.values())
        assert [i for p in got for i in _ids(got)[p]] == ["r-%d" % k for k in range(1, 7)]

    def test_one_row_over_the_cap_cannot_be_split(self, cache):
        with pytest.raises(ValueError, match="scatter-2"):
            gallery.resplit({"scatter": [_row("a-1")], "scatter-2": [_row("b-2")]},
                            {"scatter": 200, "scatter-2": 5000}, cache, cap=1000)


class TestBuildCapped:

    def test_rebuilds_only_the_split_type_until_every_page_fits(self, tmp_path, cache,
                                                                  monkeypatch):
        """A fake build writes <page>.html of 200 bytes and 100 a row; the
        row cost is uneven (s-00 costs 500), so a second round splits again."""
        out = tmp_path / "out"
        out.mkdir()
        calls = []

        def fake_build(page_rows, run_dir, out_dir, repo, jobs=3):
            calls.append(sorted(page_rows))
            got = {}
            for page, rows in page_rows.items():
                n = 200 + sum(500 if r["id"] == "s-00" else 100 for r in rows)
                (out / ("%s.html" % page)).write_bytes(b"x" * n)
                got[page] = {"log": {"build": 0}, "shown": {r["id"]: "live" for r in rows}}
            return got
        monkeypatch.setattr(gallery, "build_pages", fake_build)
        rows = [_row("s-%02d" % k) for k in range(12)]
        page_rows = {"line": [_row("l-1", plottype="line")], "scatter": rows}
        got, built = gallery.build_capped(page_rows, str(tmp_path / "run"), str(out),
                                          "/repo", 2, cache, cap=1000)
        assert calls[0] == ["line", "scatter"]
        assert all(c and all(p.startswith("scatter") for p in c) for c in calls[1:])
        assert len(calls) >= 2
        assert set(built) == set(got)
        assert [i for p in got if p != "line" for i in _ids(got)[p]] == [
            "s-%02d" % k for k in range(12)]
        on_disk = sorted(f[:-5] for f in os.listdir(out) if f.endswith(".html"))
        assert on_disk == sorted(got)
        assert all(os.path.getsize(out / ("%s.html" % p)) <= 1000 for p in got)


class TestParsePageLog:

    def test_markers_and_the_error_line(self):
        text = (". display \"##FRAME gf1 \" _rc\n##FRAME gf1 0\n##IMAGE a-1 0\n"
                "##GRAPH a-1 0\n##STATIC b-2 0\n##IMAGE b-2 603\n"
                "dash build: the layout names g9\nr(198);\n##BUILD 198\n")
        p = gallery.parse_page_log(text)
        assert p == {"frames": {"gf1": 0}, "images": {"a-1": 0, "b-2": 603},
                     "graphs": {"a-1": 0}, "static": {"b-2": 0}, "build": 198,
                     "error": "dash build: the layout names g9"}
        assert "clash" not in p
        p = gallery.parse_page_log("##BUILD 0\n")
        assert p["build"] == 0 and p["error"] is None
        assert gallery.parse_page_log("r(111);\n")["error"] == "r(111);"


class TestRunPage:

    def test_runs_the_slot_and_parses_the_log(self, tmp_path, monkeypatch):
        d = tmp_path / "p"
        d.mkdir()
        monkeypatch.setattr(twoway_run, "SLOT_CMD", _fake_slot(tmp_path, {"p": "##BUILD 0\n"}))
        assert gallery.run_page(str(d))["build"] == 0
        (d / "page.log").unlink()
        monkeypatch.setattr(twoway_run, "SLOT_CMD", _fake_slot(tmp_path, {}))
        got = gallery.run_page(str(d))
        assert got["build"] is None and got["error"] == "no page.log"


class TestBuildPages:

    def test_each_page_builds_once(self, tmp_path, monkeypatch, cache):
        calls = tmp_path / "calls.txt"
        monkeypatch.setattr(twoway_run, "SLOT_CMD",
                            _fake_slot(tmp_path, {"*": "##BUILD 0\n##GRAPH b-2 198\n"},
                                       calls))
        panelled = []
        monkeypatch.setattr(gallery, "panel_page",
                            lambda path, rows, shown: panelled.append(
                                (os.path.basename(path), [r["id"] for r in rows],
                                 dict(shown))))
        page_rows = {"scatter": [_row("a-1"), _row("b-2")], "scatter-2": [_row("c-3")],
                     "line": [_row("d-4", plottype="line")]}
        got = gallery.build_pages(page_rows, str(tmp_path / "run"), str(tmp_path / "out"),
                                  "/repo", jobs=2)
        assert sorted(calls.read_text().split()) == ["line", "scatter", "scatter-2"]
        assert set(got) == {"scatter", "scatter-2", "line"}
        assert got["scatter"]["shown"] == {"a-1": "live", "b-2": "refused"}
        assert got["line"]["log"]["build"] == 0
        # Each built page is panelled once, with what it shows.
        assert sorted(panelled) == [
            ("line.html", ["d-4"], {"d-4": "live"}),
            ("scatter-2.html", ["c-3"], {"c-3": "live"}),
            ("scatter.html", ["a-1", "b-2"], {"a-1": "live", "b-2": "refused"})]

    def test_a_failed_build_raises_naming_the_page(self, tmp_path, monkeypatch, cache):
        calls = tmp_path / "calls.txt"
        monkeypatch.setattr(twoway_run, "SLOT_CMD",
                            _fake_slot(tmp_path, {"*": "r(198);\n##BUILD 198\n"}, calls))
        with pytest.raises(RuntimeError) as e:
            gallery.build_pages({"scatter": [_row("a-1")]}, str(tmp_path / "run"),
                                str(tmp_path / "out"), "/repo")
        assert "scatter" in str(e.value) and "198" in str(e.value)
        assert "r(198);" in str(e.value)
        assert calls.read_text().split() == ["scatter"]


class TestWriteIndex:

    def test_one_linked_panel_per_page(self, tmp_path, cache):
        page_rows = {"scatter": [_row("a-1"), _row("b-2")], "scatter-2": [_row("c-3")],
                     "line": [_row("d-4", plottype="line")]}
        shown = {"a-1": "refused", "b-2": "live", "c-3": "live", "d-4": "live"}
        meta = {"generated": "22oct2026", "dash_commit": "0123456789abcdef" * 2 + "01234567"}
        idir = tmp_path / "run" / "gallery" / "_index"
        path = gallery.write_index(page_rows, shown, str(tmp_path / "out"), str(idir),
                                   "/repo", meta)
        do = open(path, encoding="utf-8").read()
        lines = [ln for ln in do.splitlines() if "dash image using" in ln]
        assert len(lines) == 3
        assert 'name(i1)' in lines[0] and 'link("scatter.html")' in lines[0]
        assert "b-2-twoway.svg" in lines[0]
        assert 'link("scatter-2.html")' in lines[1] and 'link("line.html")' in lines[2]
        assert "layout(auto)" in do and 'saving("%s/index.html")' % (tmp_path / "out") in do
        caps = (idir / "captions.txt").read_text(encoding="utf-8").splitlines()
        assert "scatter (part 1 of 2): 2 examples" in caps
        assert "scatter (part 2 of 2): 1 examples" in caps
        assert "line: 1 examples" in caps
        assert "twoway line: opens line.html" in caps
        assert caps[-1] == "4 examples twoway draws, drawn on 22oct2026 at dash commit 0123456"


class TestSwapIn:

    def test_replaces_svg_and_pages_and_leaves_nothing_stale(self, tmp_path):
        out, g = tmp_path / "out", tmp_path / "g"
        (out / "svg").mkdir(parents=True)
        (out / "svg" / "new-twoway.svg").write_text("n")
        (out / "scatter.html").write_text("p")
        (g / "svg").mkdir(parents=True)
        (g / "svg" / "old-twoway.svg").write_text("o")
        (g / "old.html").write_text("o")
        got = gallery.swap_in(str(out), str(g))
        assert got == ["scatter.html", "svg/new-twoway.svg"]
        assert sorted(os.listdir(g)) == ["scatter.html", "svg"]
        assert os.listdir(g / "svg") == ["new-twoway.svg"]
        (g / "old.html").write_text("o")
        assert gallery.swap_in(str(out), str(g), html=False) == ["svg/new-twoway.svg"]
        assert (g / "old.html").exists()


def _ex(corpus, i):
    return {e["id"]: e for e in corpus["examples"]}[i]


def _corpus(tmp_path, cache):
    run = _fake_run(tmp_path)
    rows, _ = gallery.load_run(str(run))
    out = tmp_path / "out"
    svgs = gallery.copy_svgs(rows, str(run), str(out))
    shown = {_IDS[0]: ("live", "scatter"), _IDS[1]: ("live", "scatter")}
    meta = {"generated": "22oct2026", "dash_commit": "a" * 40, "stata_version": "19.5",
            "pages": ["scatter"], "load_s": {"scatter.html": 1.25, "index.html": 0.5}}
    return gallery.corpus_json(rows, shown, svgs, meta, str(out)), rows, svgs, out


class TestCorpusJson:

    def test_every_example_with_both_answers_sorted(self, tmp_path, cache):
        corpus, rows, svgs, out = _corpus(tmp_path, cache)
        ex = corpus["examples"]
        assert [e["id"] for e in ex] == sorted(_IDS[:2])
        by = {e["id"]: e for e in ex}
        a, b, c = _IDS
        assert c not in by  # D52: twoway refuses it, so it is not in the comparison
        assert by[a]["duplicates"] == ["gpdf-scatter-dddd0004"]
        assert by[a]["ledger"] == ["AX-4"] and by[a]["checks"] == ["legend", "x_ticks"]
        assert by[a]["differences"][0]["gaps4"] == "AX-4"
        assert by[a]["dash_svg_vector"] is True and by[a]["missing"] == []
        assert by[a]["shown"] == "live" and by[a]["page"] == "scatter"
        assert by[a]["command"] == "scatter mpg weight"
        assert by[a]["dash_command"] == "dash scatter mpg weight"
        assert corpus["_meta"]["load_s"] == {"scatter.html": 1.25, "index.html": 0.5}
        n = corpus["_meta"]["counts"]
        assert n["examples"] == 2 and n["duplicates"] == 1 and n["gallery"] == 2
        assert n["Same"] + n["Close"] + n["Differs"] + n["skipped"] == n["examples"]
        assert n["live"] + n["static"] + n["refused_shown"] == n["gallery"]
        assert "refused_twoway" not in n and n["refused_dash"] == 0
        # A webuse dataset the cache lacks: shown static, its missing list read.
        {r["id"]: r for r in rows}[b]["example"]["setup"] = ["webuse lbw, clear"]
        shown = {_IDS[0]: ("live", "scatter"), _IDS[1]: ("static", "scatter")}
        corpus = gallery.corpus_json(rows, shown, svgs, corpus["_meta"], str(out))
        by = {e["id"]: e for e in corpus["examples"]}
        assert by[b]["missing"] == ["lbw"] and by[b]["shown"] == "static"
        path = gallery.write_corpus_json(corpus, str(tmp_path / "g"))
        text = open(path, encoding="utf-8").read()
        assert text.endswith("}\n") and json.loads(text) == corpus
        assert text.startswith('{\n  "_meta"')

    def test_a_left_out_example_keeps_its_comparison_off_the_gallery(self, tmp_path, cache):
        """D78: the example stays in corpus.json with its verdict; gallery
        false, on no page, no SVGs, and out of the gallery count."""
        run = _fake_run(tmp_path)
        rows, _ = gallery.load_run(str(run))
        a, b, _c = _IDS
        {r["id"]: r for r in rows}[a]["example"]["plottype"] = "contour"
        out = tmp_path / "out"
        svgs = gallery.copy_svgs(rows, str(run), str(out))
        corpus = gallery.corpus_json(rows, {b: ("live", "scatter")}, svgs,
                                     {"generated": "13nov2026"}, str(out))
        by = {e["id"]: e for e in corpus["examples"]}
        assert by[a]["verdict"] == "Close" and by[a]["gallery"] is False
        assert by[a]["shown"] is None and by[a]["page"] is None
        assert by[a]["twoway_svg"] is None and by[a]["dash_svg"] is None
        n = corpus["_meta"]["counts"]
        assert n["examples"] == 2 and n["gallery"] == 1
        assert n["live"] + n["static"] + n["refused_shown"] == n["gallery"]


class _StubProbe:

    def __init__(self):
        self.calls = []

    def navigate(self, path, ready=None):
        self.calls.append(("navigate", path))
        time.sleep(0.05)

    def eval_async(self, expr):
        self.calls.append(("eval", expr))


class TestMeasureLoad:

    def test_times_each_page_through_the_probe(self, tmp_path):
        a, b = str(tmp_path / "a.html"), str(tmp_path / "b.html")
        stub = _StubProbe()
        got = gallery.measure_load([a, b], probe=stub)
        assert list(got) == ["a.html", "b.html"]
        for v in got.values():
            assert v >= 0.05 and v == round(v, 2)
        two = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
        assert stub.calls == [("navigate", a), ("eval", two), ("navigate", b), ("eval", two)]


def _b64(s):
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


class TestVectorSvg:

    def test_raster_images_are_found(self):
        paths = '<svg><path d="M0 0"/></svg>'
        assert gallery.is_vector_svg(paths) is True
        inner = '<svg><path d="M1 1"/></svg>'
        assert gallery.is_vector_svg(
            '<svg><image href="data:image/svg+xml;base64,%s"/></svg>' % _b64(inner)) is True
        assert gallery.is_vector_svg("<svg>%s</svg>" % _PNG_IMAGE) is False
        assert gallery.is_vector_svg('<svg><IMAGE xlink:href="key.png"/></svg>') is False
        nested = "<svg>%s</svg>" % _PNG_IMAGE
        assert gallery.is_vector_svg(
            '<svg><image href="data:image/svg+xml;base64,%s"/></svg>' % _b64(nested)) is False


def _readme(tmp_path):
    p = tmp_path / "README.md"
    p.write_text("# dash\n\n## Example\n\ntext\n\n## Documentation\n\nmore\n",
                 encoding="utf-8")
    return p


class TestReadmeBlock:

    def test_pairs_escaped_twoway_left_with_date_and_commit(self, tmp_path, cache):
        corpus, _, _, _ = _corpus(tmp_path, cache)
        a = _IDS[0]
        _ex(corpus, a)["command"] = 'scatter mpg weight, title("<b>")'
        block = gallery.readme_block(corpus, [a])
        assert block.startswith("These pairs were drawn on 22oct2026 at dash commit aaaaaaa;")
        pair = [ln for ln in block.splitlines() if ln.startswith("<p><img")]
        assert len(pair) == 1
        p = pair[0]
        assert p.index("svg/%s-twoway.svg" % a) < p.index("svg/%s-dash.svg" % a)
        assert "&lt;b&gt;" in p and "&quot;" in p and "<b>\"" not in p
        assert "<b>Close</b>: x-axis ticks, legend keys</p>" in p
        assert "[docs/gallery/index.html](docs/gallery/index.html)" in block
        block = gallery.readme_block(corpus, [a], pages_url="https://example.org/g/")
        assert "the gallery pages: [https://example.org/g/](https://example.org/g/)." in block
        with pytest.raises(ValueError, match=_IDS[2]):
            gallery.readme_block(corpus, [_IDS[2]])
        with pytest.raises(ValueError, match="nope"):
            gallery.readme_block(corpus, ["nope"])

    def test_a_raster_dash_svg_stops_the_block(self, tmp_path, cache):
        corpus, _, _, _ = _corpus(tmp_path, cache)
        _ex(corpus, _IDS[0])["dash_svg_vector"] = False
        with pytest.raises(ValueError, match=_IDS[0]):
            gallery.readme_block(corpus, [_IDS[0]])

    def test_stata_terms_only(self, tmp_path, cache):
        corpus, _, _, _ = _corpus(tmp_path, cache)
        block = gallery.readme_block(corpus, [_IDS[0], _IDS[1]])
        assert "AX-4" not in block and "x_ticks" not in block
        for ln in block.splitlines():
            # The verdict text after the command; ids and paths are not captions.
            assert gallery.stata_terms_only(ln.split("</code>", 1)[-1]), ln
        _ex(corpus, _IDS[0])["summary"] = "x_ticks"
        with pytest.raises(ValueError, match=_IDS[0]):
            gallery.readme_block(corpus, [_IDS[0]])


class TestReplaceBlock:

    def test_inserts_once_then_replaces_idempotently(self, tmp_path):
        text = _readme(tmp_path).read_text(encoding="utf-8")
        once = gallery.replace_block(text, "BLOCK 1")
        assert once.count("## Gallery") == 1
        assert once.index("## Gallery") < once.index(gallery.START) < once.index("BLOCK 1")
        assert once.index(gallery.END) < once.index("## Documentation")
        assert gallery.replace_block(once, "BLOCK 1") == once
        twice = gallery.replace_block(once, "BLOCK 2")
        assert "BLOCK 1" not in twice and twice.count("## Gallery") == 1
        assert twice.replace("BLOCK 2", "BLOCK 1") == once

    def test_refuses_single_doubled_or_reversed_markers(self):
        s, e = gallery.START, gallery.END
        for bad, word in (("x\n%s\n## Documentation\n" % s, "marker"),
                          ("%s\n%s\n%s\n%s\n" % (s, e, s, e), "marker"),
                          ("%s\n%s\n" % (e, s), "before"),
                          ("# dash\nno heading\n", "Documentation")):
            with pytest.raises(ValueError, match=word):
                gallery.replace_block(bad, "B")


def _cand_corpus(tmp_path, dash_text):
    root = tmp_path / "root"
    (root / "svg").mkdir(parents=True)
    ex = []
    specs = [("h-a", "scatter", "scatter y x", True), ("h-b", "scatter", "scatter y x, by(f)",
                                                          False),
             ("h-c", "line", "line y x || lfit y x", True), ("h-d", "contour", "contour z y x",
                                                           True),
             ("h-e", "scatter", "scatter y x, colorvar(z)", True)]
    for i, pt, cmd, matched in specs:
        (root / "svg" / ("%s-twoway.svg" % i)).write_text(_TW_SVG)
        (root / "svg" / ("%s-dash.svg" % i)).write_text(dash_text.get(i, _DA_SVG))
        ex.append({"id": i, "source": "help", "plottype": pt, "command": cmd,
                   "gallery": True, "size_matched": matched, "verdict": "Differs",
                   "twoway_svg": "svg/%s-twoway.svg" % i, "dash_svg": "svg/%s-dash.svg" % i,
                   "dash_svg_vector": gallery.is_vector_svg(dash_text.get(i, _DA_SVG))})
    ex.append(dict(ex[0], id="g-a", source="gpdf"))
    ex.append(dict(ex[0], id="h-z", gallery=False))
    return {"_meta": {}, "examples": ex}, str(root)


class TestReadmeCandidates:

    def test_one_list_per_group_ignoring_verdicts(self, tmp_path):
        corpus, root = _cand_corpus(tmp_path, {})
        got = gallery.readme_candidates(corpus, root)
        assert list(got) == ["scatter", "line", "connected", "fit", "by()", "histogram",
                             "kdensity", "bar", "area", "pcarrow", "colorvar()"]
        assert got["scatter"] == ["h-a", "h-e", "h-b"]
        assert got["fit"] == ["h-c"] and got["by()"] == ["h-b"]
        assert got["colorvar()"] == ["h-e"]
        assert got["bar"] == []
        # D78: contour is left out of the gallery, so never a README pair.
        assert not any("h-d" in ids for ids in got.values())

    def test_only_fully_vector_dash_svgs(self, tmp_path):
        legend_key = ('<svg><image href="data:image/svg+xml;base64,%s"/></svg>'
                      % _b64('<svg><path d="M0 0"/></svg>'))
        corpus, root = _cand_corpus(tmp_path, {"h-a": "<svg>%s</svg>" % _PNG_IMAGE,
                                               "h-e": legend_key})
        got = gallery.readme_candidates(corpus, root)
        assert "h-a" not in got["scatter"] and "h-e" in got["scatter"]
        rows = [_row("h-a")]
        assert [r["id"] for r in gallery.pages(rows)["scatter"]] == ["h-a"]


class TestMain:

    def test_skip_build_writes_everything_but_the_pages(self, tmp_path, cache, capsys):
        run = _fake_run(tmp_path)
        g = tmp_path / "g"
        readme = _readme(tmp_path)
        ids = tmp_path / "ids.txt"
        ids.write_text("# header\n%s\n" % _IDS[0], encoding="utf-8")
        assert gallery.main(["--run", str(run), "--gallery", str(g), "--readme", str(readme),
                             "--ids", str(ids), "--skip-build"]) == 0
        assert sorted(os.listdir(g)) == ["corpus.json", "svg"]
        assert len(os.listdir(g / "svg")) == 4
        corpus = json.loads((g / "corpus.json").read_text(encoding="utf-8"))
        assert corpus["_meta"]["pages"] == ["scatter"] and corpus["_meta"]["load_s"] == {}
        assert corpus["_meta"]["stata_version"] == "19.5"
        assert {e["id"]: e["shown"] for e in corpus["examples"]} == {
            _IDS[0]: "live", _IDS[1]: "live"}
        text = readme.read_text(encoding="utf-8")
        assert text.count("## Gallery") == 1 and text.count("<p><img") == 1
        assert os.path.exists(run / "gallery" / "scatter" / "page.do")
        assert not os.path.exists(run / "gallery" / "scatter" / "page.log")

    def test_suggest_ids_reads_the_run_and_writes_nothing(self, tmp_path, cache, capsys,
                                                           monkeypatch):
        run = _fake_run(tmp_path)
        before = _tree(str(tmp_path))

        def boom(*a, **k):
            raise AssertionError("called")
        monkeypatch.setattr(gallery, "run_page", boom)
        monkeypatch.setattr(gallery, "swap_in", boom)
        assert gallery.main(["--run", str(run), "--suggest-ids"]) == 0
        out = capsys.readouterr().out
        assert _IDS[0] in out and _IDS[1] in out and _IDS[2] not in out
        assert not os.path.exists(run / "gallery")
        assert _tree(str(tmp_path)) == before

    def test_a_failed_index_build_changes_nothing(self, tmp_path, cache, monkeypatch):
        run = _fake_run(tmp_path)
        g = tmp_path / "g"
        (g / "svg").mkdir(parents=True)
        (g / "svg" / "old-twoway.svg").write_text("old")
        (g / "scatter.html").write_text("old page")
        readme = _readme(tmp_path)
        ids = tmp_path / "ids.txt"
        ids.write_text("%s\n" % _IDS[0], encoding="utf-8")
        before = _tree(str(g)), readme.read_bytes()

        def fake_run_page(page_dir):
            rc = 198 if os.path.basename(page_dir) == "_index" else 0
            if not rc:  # a built page is written as dash build writes it
                with open(os.path.join(os.path.dirname(page_dir), "out", "%s.html"
                                       % os.path.basename(page_dir)), "w") as fh:
                    fh.write("<html></html>")
            return {"frames": {}, "images": {}, "graphs": {}, "static": {}, "build": rc,
                    "error": "r(198);" if rc else None}
        monkeypatch.setattr(gallery, "run_page", fake_run_page)
        monkeypatch.setattr(gallery, "panel_page", lambda *a: 0)
        with pytest.raises(RuntimeError, match="index"):
            gallery.main(["--run", str(run), "--gallery", str(g), "--readme", str(readme),
                          "--ids", str(ids)])
        assert (_tree(str(g)), readme.read_bytes()) == before


class TestSummary:

    def test_counts_per_verdict_type_and_ledger(self, tmp_path):
        run = _fake_run(tmp_path)
        s = summary.summarise(str(run))
        # D52: the example twoway refuses is dropped, not counted as a verdict.
        assert s["examples"] == 2 and s["duplicates"] == 1 and s["gallery"] == 2
        assert s["verdicts"] == {"Close": 1, "Differs": 0, "Same": 1, "skipped": 0}
        assert s["refused"] == {"dash": 0} and s["twoway_refuses"] == 1
        assert s["by_plottype"]["scatter"] == {"Close": 1, "Differs": 0, "Same": 1,
                                               "examples": 2, "skipped": 0}
        assert s["ledger"] == {"AX-4": 1}
        assert s["unexplained"] == {}
        assert list(s) == sorted(s)

    def test_the_fixture_meta(self, tmp_path):
        run = _fake_run(tmp_path)
        out = tmp_path / "b.json"
        summary.write_fixture(summary.summarise(str(run)), str(out), str(run))
        d = json.loads(out.read_text(encoding="utf-8"))
        m = d["_meta"]
        assert set(m) == {"stata_version", "born_date", "extracted", "dash_commit", "source"}
        assert m["stata_version"] == "19.5" and m["source"] == "scripts/corpus/summary.py"
        assert re.match(r"^\d{2} [A-Z][a-z]{2} \d{4}$", m["born_date"])
        assert re.match(r"^[0-9a-f]{40}$", m["dash_commit"])
        assert d["examples"] == 2

    def test_main_prints_the_line_and_writes_out(self, tmp_path, capsys):
        run = _fake_run(tmp_path)
        assert summary.main(["--run", str(run)]) == 0
        out = capsys.readouterr().out
        assert ("corpus: 2 examples (1 duplicates removed; 1 twoway refuses): 1 Same, "
                "1 Close, 0 Differs, 0 skipped; 2 twoway draws for the gallery") in out
        b = tmp_path / "b.json"
        assert summary.main(["--run", str(run), "--out", str(b)]) == 0
        d = json.loads(b.read_text(encoding="utf-8"))
        assert len(d["_meta"]) == 5 and d["gallery"] == 2


def _make_rules():
    with open(os.path.join(_ROOT, "Makefile"), encoding="utf-8") as fh:
        mk = fh.read()
    rules = {}
    for m in re.finditer(r"^([A-Za-z][\w-]*):([^\n=]*)\n((?:\t.*\n)*)", mk, re.M):
        rules[m.group(1)] = (m.group(2), m.group(3))
    return mk, rules


class TestTheMakefile:

    def test_targets_phony_help_and_not_in_the_gates(self):
        mk, rules = _make_rules()
        assert "corpus" in rules and "gallery" in rules
        phony = re.search(r"^\.PHONY:(.*)$", mk, re.M).group(1).split()
        assert "corpus" in phony and "gallery" in phony
        assert "make corpus" in rules["help"][1] and "make gallery" in rules["help"][1]
        for stage in ("extract.py", "datasets.py --fetch", "twoway_run.py", "dash_run.py",
                      "verdict.py", "summary.py"):
            assert stage in rules["corpus"][1], stage
        assert "gallery.py" in rules["gallery"][1]
        assert "--readme README.md" in rules["gallery"][1]
        # The README links the gallery where Pages serves it (17nov2026).
        assert '--pages-url "$(GALLERY_URL)"' in rules["gallery"][1]
        assert re.search(r"^GALLERY_URL \?= %s$" % re.escape(_GALLERY_URL), mk, re.M)
        for gate in ("check", "test", "test-dev", "test-all", "cert", "gate", "release"):
            prereq, recipe = rules[gate]
            assert not re.search(r"\b(corpus|gallery)\b", prereq), gate
            assert "scripts/corpus" not in recipe and "make corpus" not in recipe, gate
            assert "make gallery" not in recipe, gate


class TestTheIgnoreRules:

    def test_gallery_files_are_not_ignored(self):
        for p in ("docs/gallery/index.html", "docs/gallery/scatter.html",
                  "docs/gallery/corpus.json"):
            r = subprocess.run(["git", "check-ignore", "-q", "--no-index", p], cwd=_ROOT)
            assert r.returncode == 1, p


def _git_ls(path):
    p = subprocess.run(["git", "-C", _ROOT, "ls-files", path], capture_output=True, text=True)
    return [ln for ln in p.stdout.splitlines() if ln]


class TestTheCommittedGallery:

    def test_the_files_agree_with_corpus_json(self):
        if not _git_ls("docs/gallery/corpus.json"):
            # Nothing is built before WP-50's closeout (P4-8).
            assert _git_ls("docs/gallery") == []
            return
        with open(os.path.join(_ROOT, "docs", "gallery", "corpus.json"), encoding="utf-8") as fh:
            corpus = json.load(fh)
        meta = corpus["_meta"]
        want = {"corpus.json", "index.html"} | {"%s.html" % p for p in meta["pages"]}
        for e in corpus["examples"]:
            want |= {e[k] for k in ("twoway_svg", "dash_svg") if e[k]}
        got = {os.path.relpath(p, "docs/gallery") for p in _git_ls("docs/gallery")}
        assert got == want
        assert set(meta["load_s"]) == {"%s.html" % p for p in meta["pages"]} | {"index.html"}
        assert all(isinstance(v, (int, float)) and v > 0 for v in meta["load_s"].values())
        n = meta["counts"]
        assert n["Same"] + n["Close"] + n["Differs"] + n["skipped"] == n["examples"]
        assert n["examples"] == len(corpus["examples"])
        assert n["live"] + n["static"] + n["refused_shown"] == n["gallery"]
        known = set(ledger.gaps4_states())
        for e in corpus["examples"]:
            assert set(e["ledger"] or []) <= known, e["id"]
            assert (e["shown"] == "static") == bool(e["missing"]), e["id"]

    def test_every_file_fits_github_and_no_left_out_type_is_paged(self):
        """D78: every committed gallery file is within the byte cap (GitHub
        refuses a file over 100 MB), and no page is of a left-out plot type."""
        files = _git_ls("docs/gallery")
        for f in files:
            assert os.path.getsize(os.path.join(_ROOT, f)) <= gallery.PAGE_BYTES_MAX, f
        if not _git_ls("docs/gallery/corpus.json"):
            return
        with open(os.path.join(_ROOT, "docs", "gallery", "corpus.json"), encoding="utf-8") as fh:
            corpus = json.load(fh)
        assert not {p.split("-")[0] for p in corpus["_meta"]["pages"]} & set(gallery.LEFT_OUT)
        for e in corpus["examples"]:
            if e["plottype"] in gallery.LEFT_OUT:
                assert not e["gallery"] and e["page"] is None, e["id"]

    def test_the_readme_block_is_the_generated_one(self):
        with open(os.path.join(_ROOT, "README.md"), encoding="utf-8") as fh:
            readme = fh.read()
        if not _git_ls("docs/gallery/corpus.json"):
            assert gallery.START not in readme and gallery.END not in readme
            return
        assert readme.count(gallery.START) == 1 and readme.count(gallery.END) == 1
        with open(os.path.join(_ROOT, "docs", "gallery", "corpus.json"), encoding="utf-8") as fh:
            corpus = json.load(fh)
        ids = gallery.read_ids(os.path.join(_ROOT, "scripts", "corpus", "readme_examples.txt"))
        assert 10 <= len(ids) <= 14
        block = gallery.readme_block(corpus, ids, pages_url=_GALLERY_URL)
        assert gallery.replace_block(readme, block) == readme
