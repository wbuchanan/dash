"""
test_corpus_dash.py -- the corpus's dash runner (WP-33 33-04).

scripts/corpus/dash_run.py runs every corpus example's dash command in Stata
with saving() appended (chunks through scripts/stata_slot.sh, as the twoway
runner does), then opens each saved page in one headless Chrome, sizes the
figure to twoway's size, exports Bokeh's own SVG, dumps the drawn views and
normalises the SVG.  The default-tier tests drive run_stata with a fake slot
command and export_pages with a stub probe; TestInChrome (release tier) reads
real pages.
"""
import json
import os
import re
import sys
import warnings

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HERE = os.path.join(_ROOT, "test")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402
from scripts.corpus import dash_run, twoway_run  # noqa: E402


def _ex(i, cmd="dash scatter mpg weight", setup=("sysuse auto, clear",), plottype="scatter"):
    return {"id": i, "cmd": cmd.replace("dash ", "twoway ", 1), "dash_cmd": cmd,
            "setup": list(setup), "plottype": plottype}


def _tw(i, rc=0, skip=None, w=7.5, h=4.5):
    r = dict.fromkeys(twoway_run.ROW_KEYS)
    r.update(id=i, rc=rc, skip=skip, width_in=w if rc == 0 else None,
             height_in=h if rc == 0 else None)
    return r


def _write_run(run, examples, tw_rows):
    run.mkdir(parents=True, exist_ok=True)
    with open(run / "examples.jsonl", "w", encoding="utf-8") as fh:
        for e in examples:
            fh.write(json.dumps(e) + "\n")
    with open(run / "twoway.jsonl", "w", encoding="utf-8") as fh:
        for r in tw_rows:
            fh.write(json.dumps(r) + "\n")


def _rows(run):
    with open(run / "dash.jsonl", encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


class TestWithSaving:

    def test_comma_rules(self):
        p = "/r/dash/a.html"
        s = 'saving("/r/dash/a.html", replace)'
        cases = [
            ("dash scatter mpg weight", "dash scatter mpg weight, " + s),
            ('dash scatter mpg weight, title("a")', 'dash scatter mpg weight, title("a") ' + s),
            ("dash (scatter y x, mc(red))", "dash (scatter y x, mc(red)), " + s),
            ("dash (scatter y x, mc(red)) (line y x), xtitle(t)",
             "dash (scatter y x, mc(red)) (line y x), xtitle(t) " + s),
            ('dash scatter y x if s == "a, b"', 'dash scatter y x if s == "a, b", ' + s),
            ("dash scatter y x if s == `\"a, b\"'", "dash scatter y x if s == `\"a, b\"', " + s),
            ("dash scatter y x  ", "dash scatter y x, " + s),
            # || plots: only the last plot's comma counts.  Flipped (D57): a
            # trailing || stays, saving() follows it as twoway's grammar takes it.
            ("dash line a y, || line b y || lfit d y", "dash line a y, || line b y || lfit d y, "
             + s),
            ("dash spike c d || bar v d, yaxis(2) ||",
             "dash spike c d || bar v d, yaxis(2) || , " + s),
            ('dash scatter y x, title("a || b")', 'dash scatter y x, title("a || b") ' + s),
        ]
        for cmd, want in cases:
            assert dash_run.with_saving(cmd, p) == want, cmd


class TestCommandIdentity:
    # D57: the runners pass each command through unchanged; dash's gets only
    # saving(), where twoway's grammar puts a graph option.  A command ending
    # in || keeps it: twoway and dash both take `... || , saving(...)`
    # (measured 23oct2026).

    _PAIRS = (("twoway scatter mpg weight, ms(oh) ||", "dash scatter mpg weight, ms(oh) ||"),
              ("scatter open close, msize(*.25) ||", "dash scatter open close, msize(*.25) ||"),
              ('twoway line le year, title("a, b")', 'dash line le year, title("a, b")'),
              ("twoway (scatter mpg weight) (lfit mpg weight)",
               "dash (scatter mpg weight) (lfit mpg weight)"))

    def _cmds(self, tmp_path, ex):
        tw = [ln[len("capture noisily "):] for ln in
              twoway_run.do_text(ex, str(tmp_path), str(tmp_path)).split("\n")
              if ln.startswith("capture noisily ") and "graph export" not in ln
              and not ln.startswith("capture noisily {")]
        da = [ln[len("capture noisily "):] for ln in
              dash_run.do_text(ex, str(tmp_path), str(tmp_path), _ROOT).split("\n")
              if ln.startswith("capture noisily ") and not ln.startswith("capture noisily {")]
        return tw, da

    def test_the_runners_change_nothing_but_saving(self, tmp_path):
        ex = [dict(_ex("e%d" % k, cmd=d), cmd=t) for k, (t, d) in enumerate(self._PAIRS)]
        tw, da = self._cmds(tmp_path, ex)
        assert len(tw) == len(da) == len(self._PAIRS)
        for t, d in zip(tw, da):
            d = re.sub(r'\s*,?\s*saving\("[^"]*", replace\)$', "", d)
            assert re.sub(r"^(?:graph twoway|twoway)\s+", "", t) == d[len("dash "):], (t, d)
        assert dash_run.with_saving("dash scatter mpg weight, ms(oh) ||", "p") == \
            'dash scatter mpg weight, ms(oh) || , saving("p", replace)'

    def test_a_session_only_python(self, tmp_path, monkeypatch):
        ex = [_ex("e1")]
        monkeypatch.delenv("DASH_CORPUS_PYTHON_EXEC", raising=False)
        assert "python_exec" not in dash_run.do_text(ex, str(tmp_path), str(tmp_path), _ROOT)
        monkeypatch.setenv("DASH_CORPUS_PYTHON_EXEC", "/opt/anaconda3/bin/python3")
        text = dash_run.do_text(ex, str(tmp_path), str(tmp_path), _ROOT)
        assert 'set python_exec "/opt/anaconda3/bin/python3"' in text.split("\n")
        assert "permanently" not in text

    def test_a_mismatched_pair_is_refused(self, tmp_path):
        bad = [dict(_ex("e1", cmd="dash scatter open close"), cmd="twoway scatter open close ||")]
        with pytest.raises(ValueError):
            twoway_run.do_text(bad, str(tmp_path), str(tmp_path))
        with pytest.raises(ValueError):
            dash_run.do_text(bad, str(tmp_path), str(tmp_path), _ROOT)
        assert twoway_run.invalid_pairs(bad) == {
            "e1": "invalid pair: the commands differ beyond twoway/dash (D57)"}


class TestDoText:

    def test_dash_lines(self, tmp_path):
        cache = str(tmp_path / "cache")
        exs = [_ex("a", setup=["webuse lbw, clear"], cmd="dash scatter bwt age"),
               _ex("b", setup=[], cmd="dash function y = x, range(0 1)")]
        text = dash_run.do_text(exs, "/o", cache, "/repo")
        lines = text.splitlines()
        assert lines[:6] == ["version 19", 'adopath ++ "/repo/"', "global dash_nobrowser 1",
                             "set more off", "set linesize 255",
                             'display "##VERSION " c(stata_version)']
        assert 'use "%s/lbw.dta", clear' % cache in lines
        assert 'capture noisily dash scatter bwt age, saving("/o/a.html", replace)' in lines
        assert 'capture noisily dash function y = x, range(0 1) saving("/o/b.html", replace)' \
            in lines
        i = lines.index('capture noisily dash scatter bwt age, saving("/o/a.html", replace)')
        assert lines[i + 1] == 'display "##RC a " _rc'
        assert lines.index('display "##BEGIN a"') < lines.index('display "##SETUP a " _rc') < i
        assert lines.index('display "##BEGIN b"') > i
        for word in ("graph export", "##EXPORT", "scheme", "graph set", "permanently"):
            assert word not in text


_CANNED = """\
##VERSION 19.5
##BEGIN a
##SETUP a 0
. capture noisily dash scatter mpg weight, saving("x", replace)
dash: dashboard saved to /x/dash/a.html
##RC a 0
##BEGIN b
##SETUP b 0
. capture noisily dash scatter mpg weight, nosuch saving("x", replace)
option nosuch not allowed
##RC b 198
"""


class TestRecords:

    def test_rows_from_a_parsed_log(self, tmp_path):
        run = tmp_path / "run"
        html = run / "dash"
        html.mkdir(parents=True)
        (html / "a.html").write_text("<html></html>")
        exs = [_ex("a"), _ex("b"), _ex("c"), _ex("d")]
        tw = {"a": _tw("a"), "b": _tw("b"), "c": _tw("c", rc=None, skip="setup rc 601")}
        parsed = twoway_run.parse_log(_CANNED)
        rows = {r["id"]: r for r in dash_run.records(exs, parsed, str(html), str(run), tw)}
        assert rows["a"]["html"] == "dash/a.html" and rows["a"]["rc"] == 0
        assert rows["a"]["skip"] is None and rows["a"]["setup_rc"] == 0
        # The harness's own saving() confirmation is not the example's message.
        assert rows["a"]["first_line"] is None
        assert rows["b"]["rc"] == 198 and rows["b"]["html"] is None
        assert rows["b"]["first_line"] == "option nosuch not allowed"
        assert rows["c"]["skip"] == "setup rc 601" and rows["c"]["rc"] is None
        assert rows["d"]["skip"] == "no twoway record"
        assert list(rows["a"]) == list(dash_run.ROW_KEYS)


def _fake_slot(tmp_path, log_text, html_ids=()):
    """A fake slot command: copies a canned log into the chunk folder and
    writes each named page beside it, as dash's saving() would."""
    log = tmp_path / "canned.log"
    log.write_text(log_text)
    touch = "".join('echo "<html></html>" > "$1/../%s.html"; ' % i for i in html_ids)
    return ["sh", "-c", 'cp "%s" "$1/dash.log"; %sexit 0' % (log, touch), "sh"]


class TestRunStata:

    def test_missing_datasets_are_named_once_and_never_run(self, tmp_path, monkeypatch,
                                                            capsys):
        cache = tmp_path / "cache"
        cache.mkdir()
        monkeypatch.setenv("DASH_CORPUS_CACHE", str(cache))
        run = tmp_path / "run"
        exs = [_ex("a", setup=["webuse lbw, clear"], cmd="dash scatter bwt age"),
               _ex("b", setup=["webuse lbw, clear", "webuse nlswork, clear"],
                   cmd="dash scatter ln_wage age"),
               _ex("c")]
        _write_run(run, exs, [_tw("a"), _tw("b"), _tw("c")])
        log = "##VERSION 19.5\n##BEGIN c\n##SETUP c 0\n##RC c 0\n"
        monkeypatch.setattr(twoway_run, "SLOT_CMD", _fake_slot(tmp_path, log, ["c"]))
        counts = dash_run.run_stata(str(run))
        out = capsys.readouterr().out
        assert out.count("skip: dataset lbw not cached") == 1
        assert out.count("skip: dataset nlswork not cached") == 1
        assert out.index("dataset lbw") < out.index("dataset nlswork")
        dos = sorted((run / "dash").glob("c*/dash.do"))
        assert len(dos) == 1
        text = dos[0].read_text()
        assert "##BEGIN a" not in text and "##BEGIN b" not in text
        assert "bwt" not in text and "ln_wage" not in text and "##BEGIN c" in text
        rows = {r["id"]: r for r in _rows(run)}
        for i in ("a", "b"):
            assert rows[i]["rc"] is None and rows[i]["html"] is None
            assert rows[i]["skip"] == "dataset lbw not cached"
        assert rows["c"]["rc"] == 0 and rows["c"]["html"] == "dash/c.html"
        assert list(rows["c"]) == list(dash_run.JSONL_KEYS)
        assert counts == {"rc0": 1, "refused": 0, "skipped": 2}
        assert str(tmp_path) not in (run / "dash.jsonl").read_text()


class TestOnlyWhatTwowayDraws:

    def test_an_example_twoway_refuses_is_not_run(self, tmp_path, monkeypatch):
        # D52: dash runs only the examples twoway accepts; a refused one has no row.
        cache = tmp_path / "cache"
        cache.mkdir()
        monkeypatch.setenv("DASH_CORPUS_CACHE", str(cache))
        run = tmp_path / "run"
        _write_run(run, [_ex("a", cmd="dash scatter mpg weight, nosuch"), _ex("c")],
                   [_tw("a", rc=198), _tw("c")])
        log = "##VERSION 19.5\n##BEGIN c\n##SETUP c 0\n##RC c 0\n"
        monkeypatch.setattr(twoway_run, "SLOT_CMD", _fake_slot(tmp_path, log, ["c"]))
        counts = dash_run.run_stata(str(run))
        text = sorted((run / "dash").glob("c*/dash.do"))[0].read_text()
        assert "##BEGIN a" not in text and "##BEGIN c" in text
        assert [r["id"] for r in _rows(run)] == ["c"]
        assert counts == {"rc0": 1, "refused": 0, "skipped": 0}


class TestNormalise:

    def test_texts_and_ids(self):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
               '<defs><clipPath id="ngWPXGKbisGz"><path d="M0 0"/></clipPath>'
               '<clipPath id="QmKa7"><path d="M1 1"/></clipPath></defs>'
               '<g clip-path="url(#ngWPXGKbisGz)"><text fill="rgb(0,0,0)" x="1">Mileage</text>'
               '<text fill="none" stroke-opacity="0" x="1">Mileage</text></g>'
               '<g clip-path="url(#QmKa7)"><use xlink:href="#QmKa7"/><use href="#ngWPXGKbisGz"/>'
               '<image href="data:image/png;base64,AAAA"/></g></svg>')
        out = dash_run.normalise_svg(svg)
        assert out == ('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
                       '<defs><clipPath id="d1"><path d="M0 0"/></clipPath>'
                       '<clipPath id="d2"><path d="M1 1"/></clipPath></defs>'
                       '<g clip-path="url(#d1)"><text fill="rgb(0,0,0)" x="1">Mileage</text>'
                       '</g>'
                       '<g clip-path="url(#d2)"><use xlink:href="#d2"/><use href="#d1"/>'
                       '<image href="data:image/png;base64,AAAA"/></g></svg>')
        assert dash_run.normalise_svg(out) == out


class TestLetterbox:

    def test_scale_and_offset(self):
        inner = '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="300"><g/></svg>'
        out = dash_run.letterbox(inner, 720, 432)
        assert out == ('<svg xmlns="http://www.w3.org/2000/svg" width="720" height="432" '
                       'viewBox="0 0 720 432"><g transform="translate(0,96) scale(0.8)">'
                       + inner + '</g></svg>')
        tall = '<?xml version="1.0"?><svg width="300px" height="600px"></svg>'
        assert 'translate(252,0) scale(0.72)' in dash_run.letterbox(tall, 720, 432)


class _StubProbe:
    """Canned answers for export_page: a lone figure for good.html, an
    exception for bad.html."""

    def __init__(self):
        self.calls = []
        self.page = None

    def navigate(self, path, ready=None):
        self.calls.append(("navigate", os.path.basename(path)))
        self.page = os.path.basename(path)

    def viewport(self, w=None, h=None):
        self.calls.append(("viewport", w, h))

    def js_errors(self):
        return ["old error"]

    def errors_since(self, n):
        return ["old error"][n:]

    def eval_async(self, expr):
        if self.page == "bad.html":
            raise RuntimeError("the page did not load")
        if expr.startswith("(" + dash_run.SIZE_JS):
            return {"lone": True, "tex": False}
        if expr.startswith("(" + dash_run.EXPORT_JS):
            return ('<svg width="720" height="432"><clipPath id="zz"/>'
                    '<text fill="#000">t</text><text fill="none">t</text></svg>')
        if expr.startswith("(" + dash_run.DUMP_JS):
            return json.dumps({"figures": [{"id": "p1"}]})
        raise AssertionError(expr[:40])


class TestExportPages:

    def test_writes_svg_and_view_per_page(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dash_run, "SETTLE_S", (0.0, 0.0))
        out = tmp_path / "out"
        pages = {"good": str(tmp_path / "good.html"), "bad": str(tmp_path / "bad.html")}
        got = dash_run.export_pages(pages, {"good": (720, 432), "bad": (720, 432)},
                                    str(out), probe=_StubProbe())
        assert got["bad"] == {"error": "the page did not load"}
        g = got["good"]
        assert g == {"svg": str(out / "good.svg"), "view": str(out / "good.view.json"),
                     "size_matched": True, "js_errors": [], "w": 720, "h": 432}
        assert (out / "good.svg").read_text() == \
            '<svg width="720" height="432"><clipPath id="d1"/><text fill="#000">t</text></svg>'
        assert json.loads((out / "good.view.json").read_text()) == {"figures": [{"id": "p1"}]}
        assert sorted(p.name for p in out.iterdir()) == ["good.svg", "good.view.json"]


def _fake_export(calls):
    def fake(pages, sizes, out_dir, probe=None):
        calls.append((dict(pages), dict(sizes), out_dir))
        out = {}
        for i in pages:
            if i == "bad":
                out[i] = {"error": "boom at %s" % pages[i]}
            else:
                out[i] = {"svg": os.path.join(out_dir, i + ".svg"),
                          "view": os.path.join(out_dir, i + ".view.json"),
                          "size_matched": i == "a", "js_errors": [], "w": sizes[i][0],
                          "h": sizes[i][1]}
        return out
    return fake


def _chrome_run(tmp_path):
    run = tmp_path / "run"
    exs = [_ex("a"), _ex("b"), _ex("bad"), _ex("r")]
    _write_run(run, exs, [_tw("a"), _tw("b", w=10.0, h=2.0), _tw("bad"), _tw("r")])
    rows = [dict(dash_run._row("a", rc=0, html="dash/a.html")),
            dict(dash_run._row("b", rc=0, html="dash/b.html")),
            dict(dash_run._row("bad", rc=0, html="dash/bad.html")),
            dict(dash_run._row("r", rc=198, first_line="option nosuch not allowed"))]
    dash_run._write_rows(str(run), rows)
    return run


class TestRunChrome:

    def test_sizes_and_rows(self, tmp_path, monkeypatch):
        run = _chrome_run(tmp_path)
        calls = []
        monkeypatch.setattr(dash_run, "export_pages", _fake_export(calls))
        counts = dash_run.run_chrome(str(run))
        assert counts == {"exported": 2, "size_matched": 1, "letterboxed": 1, "errors": 1}
        pages, sizes, out_dir = calls[0]
        assert sorted(pages) == ["a", "b", "bad"]
        assert sizes == {"a": (720, 432), "b": (960, 192), "bad": (720, 432)}
        assert out_dir == os.path.join(str(run), "dash")
        rows = {r["id"]: r for r in _rows(run)}
        assert rows["a"]["svg"] == "dash/a.svg" and rows["a"]["view"] == "dash/a.view.json"
        assert rows["a"]["size_matched"] is True and rows["b"]["size_matched"] is False
        assert (rows["b"]["w"], rows["b"]["h"]) == (960, 192)
        assert rows["bad"]["export_error"] == "boom at <run>/dash/bad.html"
        assert rows["bad"]["svg"] is None and rows["r"]["svg"] is None
        assert str(tmp_path) not in (run / "dash.jsonl").read_text()


class TestMain:

    def test_cli_chrome_only_prints_the_counts(self, tmp_path, monkeypatch, capsys):
        run = _chrome_run(tmp_path)
        calls = []
        monkeypatch.setattr(dash_run, "export_pages", _fake_export(calls))
        monkeypatch.setattr(twoway_run, "SLOT_CMD", ["sh", "-c", "exit 9", "sh"])
        assert dash_run.main(["--run", str(run), "--chrome-only", "--only", "a,r"]) == 0
        assert [sorted(c[0]) for c in calls] == [["a"]]
        out = capsys.readouterr().out
        assert "corpus: dash exported 1 (size-matched 1, letterboxed 0), errors 0" in out
        assert "corpus: dash rc0" not in out


# ---- release tier: real pages in headless Chrome ---------------------------

def _page(tmp_path, spec, name="page.html"):
    import dash_render as dr
    import test_default_axes as tda
    _tag, sp, dp = tda._write(spec)
    out = str(tmp_path / name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        html = dr.DashRenderer(sp, dp, out).render()
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out


def _two_scatters():
    import test_default_axes as tda
    return tda._spec([tda.P("scatter", "mpg", "weight"), tda.P("scatter", "turn", "weight")])


_ROOT_SVG = re.compile(r"<svg\b[^>]*>")
# D49: a Scatter's marker size joins the dump ("size", null for other glyphs).
# D56: a Scatter's drawn points ("drawn": their count and extents) join it.
_RENDERER_KEYS = {"glyph", "n", "x", "y", "marker", "fill", "line", "line_width",
                  "fill_alpha", "line_alpha", "visible", "size", "drawn"}


@pytest.mark.release
@pytest.mark.skipif(responsive_probe.find_chrome() is None,
                    reason="headless Chrome is not installed (set DASH_CHROME)")
class TestInChrome:

    def test_a_plain_page_with_its_own_ready(self, tmp_path):
        one, two = tmp_path / "one.html", tmp_path / "two.html"
        one.write_text("<html><head><title>one</title></head><body>1</body></html>")
        two.write_text("<html><head><title>two</title></head><body>2</body></html>")
        ready = "document.readyState === 'complete'"
        with dash_run.CorpusProbe(str(one), ready=ready) as p:
            assert p._eval("document.title") == "one"
            assert p.navigate(str(two), ready=ready) == "two"
            assert p.errors_since(0) == []

    def test_a_lone_figure_at_twoways_size(self, tmp_path):
        page = _page(tmp_path, _two_scatters())
        with dash_run.CorpusProbe(page, timeout=120) as p:
            got = dash_run.export_page(p, page, 720, 432)
        root = _ROOT_SVG.search(got["svg"]).group(0)
        assert 'width="720"' in root and 'height="432"' in root, root
        assert got["size_matched"] is True and got["js_errors"] == []
        figs = got["view"]["figures"]
        assert len(figs) == 1
        assert any(a["ticks"] for a in figs[0]["axes"])
        rs = figs[0]["renderers"]
        assert all(set(r) == _RENDERER_KEYS for r in rs), rs
        assert any(r["n"] and r["n"] > 0 and r["marker"] == "circle" for r in rs), rs
        assert all(r["visible"] is True for r in rs)
        sizes = [r["size"] for r in rs if r["glyph"] == "Scatter"]
        assert sizes and all(isinstance(z, dict) and z["value"] > 0 for z in sizes), sizes

    def test_a_scatter_counts_the_points_it_draws(self, tmp_path):
        # D56: rep78 is missing for five cars; the source holds 74 rows, the
        # scatter draws 69 markers.
        import test_default_axes as tda
        page = _page(tmp_path, tda._spec([tda.P("scatter", "rep78", "weight")]))
        with dash_run.CorpusProbe(page, timeout=120) as p:
            got = dash_run.export_page(p, page, 720, 432)
        sc = [r for r in got["view"]["figures"][0]["renderers"] if r["glyph"] == "Scatter"]
        assert [r["drawn"]["n"] for r in sc] == [69], sc
        assert sc[0]["drawn"]["y"] == [1, 5]

    def test_each_axis_has_its_scale_and_tick_pixels(self, tmp_path):
        # D46: the dump names each axis's scale and where its ticks are drawn.
        import test_default_axes as tda
        page = _page(tmp_path, tda._spec([tda.P("scatter", "price", "weight")],
                                         {"yscale": "log"}))
        with dash_run.CorpusProbe(page, timeout=120) as p:
            got = dash_run.export_page(p, page, 720, 432)
        axes = {a["dim"]: a for a in got["view"]["figures"][0]["axes"]}
        assert axes[0]["scale"] == "linear" and axes[1]["scale"] == "log", axes
        for a in axes.values():
            assert len(a["tick_px"]) == len(a["ticks"]) and a["ticks"], a
        xs = axes[0]["tick_px"]
        assert xs == sorted(xs) and xs[0] < xs[-1]
        # A log axis spaces 1000 .. 10000 like 10000 .. 100000, not linearly.
        frame = got["view"]["figures"][0]["frame"]
        assert all(frame[1] - 1 <= y <= frame[1] + frame[3] + 1 for y in axes[1]["tick_px"])

    def test_a_by_grid_is_letterboxed(self, tmp_path):
        import test_default_axes as tda
        page = _page(tmp_path, tda._spec([tda.P("scatter", "mpg", "weight")],
                                         {"by": "foreign"}))
        with dash_run.CorpusProbe(page, timeout=120) as p:
            got = dash_run.export_page(p, page, 720, 432)
        root = _ROOT_SVG.search(got["svg"]).group(0)
        assert root == ('<svg xmlns="http://www.w3.org/2000/svg" width="720" height="432" '
                        'viewBox="0 0 720 432">'), root
        assert got["size_matched"] is False and got["js_errors"] == []
        assert len(got["view"]["figures"]) >= 2
        assert "<path" in got["svg"]

    def test_the_export_is_deterministic(self, tmp_path):
        page = _page(tmp_path, _two_scatters())
        out = []
        for _ in range(2):
            with dash_run.CorpusProbe(page, timeout=120) as p:
                out.append(dash_run.normalise_svg(dash_run.export_page(p, page, 720, 432)["svg"]))
        assert out[0] == out[1]
        assert 'id="d1"' in out[0] and 'fill="none" stroke-opacity' not in out[0]
