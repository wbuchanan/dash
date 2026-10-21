"""test_image_panel.py -- dash image: a registered SVG panel (WP-33 33-06).

``dash image using <file.svg>, name(<n>) [caption() alt() link(<page>.html)]``
registers a picture that layout() and tabs() place like a KPI card.  The
SVG is checked when registered and again at build (no script, event
handler, foreignObject, DOCTYPE, entity or external reference), read once
at build into a ``data:image/svg+xml;base64`` address, and drawn as an
``<img>`` inside a Bokeh Div by one builder, ``_dash_image_div``, which the
served app carries by name.  No file is refused for its size (DECISIONS
A-18); only their number is bounded, by ``$dash_max_images``.
"""
import base64
import importlib.util
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import Div, TabPanel, Tabs

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, render_models  # noqa: E402

_SMOKE = os.path.join(_HERE, "fixtures", "svg_truth_smoke.svg")
_NS = 'xmlns="http://www.w3.org/2000/svg"'
_PNG = ("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAf"
        "FcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")


def _svg(body="", root_attrs=""):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg {_NS} xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="10" height="10" {root_attrs}>{body}</svg>').encode()


def _put(tmp_path, data, name="p.svg"):
    p = tmp_path / name
    p.write_bytes(data)
    return str(p)


def _uri(data):
    return "data:image/svg+xml;base64," + base64.b64encode(data).decode()


# ---------------------------------------------------------------------------
# The check
# ---------------------------------------------------------------------------

_REFUSED = [
    ("script", _svg("<script>alert(1)</script>")),
    ("script in another namespace",
     _svg('<h:script xmlns:h="http://www.w3.org/1999/xhtml">x</h:script>')),
    ("onload", _svg("", 'onload="alert(1)"')),
    ("ONCLICK on a child", _svg('<rect ONCLICK="x" width="1" height="1"/>')),
    ("foreignObject", _svg("<foreignObject><p>x</p></foreignObject>")),
    ("external href", _svg('<a href="http://x"><rect width="1" height="1"/></a>')),
    ("external xlink:href", _svg('<image xlink:href="http://x/a.png"/>')),
    ("external url() in style",
     _svg('<rect style="fill:url(http://x)" width="1" height="1"/>')),
    ("external url() in a style element",
     _svg("<style>rect { fill: url(http://x/y) }</style>")),
    ("@import", _svg("<style>@import 'http://x/a.css';</style>")),
    ("javascript:", _svg('<a href="#a" title="javascript:x"/>')),
    ("DOCTYPE", b'<?xml version="1.0"?><!DOCTYPE svg><svg ' + _NS.encode()
     + b"/>"),
    ("ENTITY", b'<?xml version="1.0"?><!ENTITY x "y"><svg ' + _NS.encode()
     + b"/>"),
    ("not XML", b"<svg " + _NS.encode() + b"><rect></svg>"),
    ("root html", b'<html xmlns="http://www.w3.org/1999/xhtml"/>'),
    ("root svg outside the namespace", b"<svg/>"),
    ("not UTF-8", b"<svg " + _NS.encode() + b"><desc>\xff</desc></svg>"),
    ("a stylesheet instruction",
     b'<?xml-stylesheet href="http://x/a.css"?><svg ' + _NS.encode() + b"/>"),
    ("set to an external href",
     _svg('<a href="#a"><set attributeName="href" to="http://x"/></a>')),
]


class TestTheCheck:

    @pytest.mark.parametrize("what,data", _REFUSED, ids=[c[0] for c in _REFUSED])
    def test_refusals(self, tmp_path, what, data):
        got = dr._dash_image_check(_put(tmp_path, data, "pic.svg"))
        assert got.startswith("198 dash image: pic.svg holds "), (what, got)
        assert got.endswith("; an image panel takes an SVG with no script, "
                            "event handler, foreignObject or external "
                            "reference."), got
        assert dr._dash_image_problem(data), what

    def test_a_missing_file_is_601_in_statas_words(self, tmp_path):
        got = dr._dash_image_check(str(tmp_path / "sub" / "gone.svg"))
        assert got == "601 file gone.svg not found", got

    def test_accepts_twoway_and_bokeh_svgs(self, tmp_path):
        assert dr._dash_image_check(_SMOKE) == ""
        bokeh = _svg(f'<defs><clipPath id="c"><rect width="1" height="1"/>'
                     f'</clipPath></defs><g clip-path="url(#c)">'
                     f'<image href="{_PNG}" width="1" height="1"/>'
                     f'<use xlink:href="#c"/></g>')
        assert dr._dash_image_check(_put(tmp_path, bokeh)) == ""
        # No per-image byte bound (DECISIONS A-18): a valid SVG past
        # 10,000,000 bytes is accepted, read whole.
        big = _svg("<!-- " + "x" * 10_000_100 + " -->")
        assert len(big) > 10_000_000
        assert dr._dash_image_check(_put(tmp_path, big, "big.svg")) == ""
        assert dr._dash_image_problem(big) is None

    def test_there_is_no_size_constant(self):
        assert not hasattr(dr, "_DASH_IMAGE_MAX_BYTES")


# ---------------------------------------------------------------------------
# The markup
# ---------------------------------------------------------------------------

_URI = _uri(_svg('<rect width="1" height="1"/>'))


class TestTheMarkup:

    def test_escaping(self):
        h = dr._dash_image_html(_URI, "<b>&\"'", 'x" onerror="y')
        assert "<figcaption>&lt;b&gt;&amp;&quot;&#x27;</figcaption>" in h
        assert 'alt="x&quot; onerror=&quot;y"' in h
        assert 'aria-label="x&quot; onerror=&quot;y"' in h
        assert "<b>" not in h and 'onerror="' not in h
        assert h.startswith('<figure class="dash-image" role="group"')
        assert f'<img src="{_URI}" ' in h
        # No caption, no figcaption.
        assert "figcaption" not in dr._dash_image_html(_URI, "", "a")
        for bad in ("javascript:alert(1)", "data:text/html;base64,PGI+",
                    "http://x/a.svg", _URI + '" onerror="x',
                    "data:image/svg+xml;base64,"):
            with pytest.raises(ValueError):
                dr._dash_image_html(bad, "c", "a")

    def test_link_wraps_the_img(self):
        h = dr._dash_image_html(_URI, "c", "a", "scatter.html")
        assert '<a href="scatter.html"><img ' in h
        assert "</a><figcaption>" in h
        plain = dr._dash_image_html(_URI, "c", "a", "")
        assert "<a" not in plain
        assert plain == dr._dash_image_html(_URI, "c", "a")
        assert dr._dash_image_link_ok("scatter.html")
        assert dr._dash_image_link_ok("Two-way_1.html")
        for bad in ("javascript:x.html", "http://x.org/p.html", "../p.html",
                    "a/b.html", "p.htm", "a b.html", "p.html\n", "", ".html",
                    'p".html', None):
            assert not dr._dash_image_link_ok(bad), bad
            if bad:
                with pytest.raises(ValueError):
                    dr._dash_image_html(_URI, "c", "a", bad)

    def test_the_div(self):
        d = dr._dash_image_div({"name": "im1", "uri": _URI, "caption": "Cap",
                                "alt": "", "link": "p.html"})
        assert isinstance(d, Div)
        assert d.disable_math is True and d.sizing_mode == "stretch_width"
        # alt() defaults to the caption, else the name.
        assert 'alt="Cap"' in d.text and '<a href="p.html">' in d.text
        assert d.html_attributes == {"role": "group", "aria-label": "Cap"}
        d2 = dr._dash_image_div({"name": "im1", "uri": _URI})
        assert 'alt="im1"' in d2.text and "<a" not in d2.text


# ---------------------------------------------------------------------------
# Resolve
# ---------------------------------------------------------------------------

class TestResolve:

    def test_uri_and_no_path(self, tmp_path):
        data = _svg('<rect width="1" height="1"/>')
        p = _put(tmp_path, data)
        got = dr._dash_resolve_images([{"name": "im1", "path": p,
                                        "caption": "c", "alt": "a",
                                        "link": "x.html"}])
        assert got == [{"name": "im1", "caption": "c", "alt": "a",
                        "link": "x.html", "uri": _uri(data)}]
        assert dr._dash_resolve_images(None) == []

    def test_a_refused_file_raises_with_the_checks_words(self, tmp_path):
        p = _put(tmp_path, _svg("<script>x</script>"), "bad.svg")
        with pytest.raises(dr.DashLimitError, match="bad.svg holds"):
            dr._dash_resolve_images([{"name": "im1", "path": p}])
        with pytest.raises(dr.DashLimitError, match="file gone.svg not found"):
            dr._dash_resolve_images([{"name": "im1",
                                      "path": str(tmp_path / "gone.svg")}])


# ---------------------------------------------------------------------------
# Both pages
# ---------------------------------------------------------------------------

def _frame():
    i = np.arange(12, dtype=float)
    return pd.DataFrame({"mpg": 12.0 + i, "weight": 2000.0 + 100.0 * i})


def _spec(tmp_path, images=True, **bo):
    build = {"layout": "auto", "link": "", "theme": "", "title": "",
             "subtitle": "", "filter": "", "tabs": "",
             "registry": "g1 im1" if images else "g1"}
    build.update(bo)
    spec = {"graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "plots": [{"type": "scatter", "yvar": "mpg",
                                   "xvar": "weight", "options": {}}],
                        "if_expr": "", "in_expr": ""}],
            "kpis": [], "build_options": build}
    if images:
        spec["images"] = [{"name": "im1", "path": _SMOKE, "caption": "Twoway",
                           "alt": "twoway's picture", "link": "scatter.html"}]
    sp, dp = tmp_path / "spec.json", tmp_path / "data.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(_frame())))
    return str(sp), str(dp)


def _models(root):
    return list(root.references()) if root is not None else []


def _image_divs(models):
    return [m for m in models if isinstance(m, Div)
            and '<figure class="dash-image"' in (m.text or "")]


def _served_doc(tmp_path, sp, dp):
    ap = tmp_path / "app.py"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(str(ap))
        ms = importlib.util.spec_from_file_location("_img_app", str(ap))
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
        doc = Document()
        mod.make_document(doc)
    return doc, ap.read_text()


class TestTheSavedPage:

    @pytest.mark.parametrize("bo", [{"layout": "1 2"},
                                    {"tabs": "A: g1 / B: im1"}],
                             ids=["layout", "tabs"])
    def test_layout_and_tabs(self, tmp_path, bo):
        sp, dp = _spec(tmp_path, **bo)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = render_models(dr.DashRenderer(sp, dp))
        assert "path" not in r.master_spec["images"][0]
        models = _models(r._last_layout_root)
        divs = _image_divs(models)
        assert len(divs) == 1, divs
        assert '<a href="scatter.html"><img src="data:image/svg+xml;base64,' \
            in divs[0].text
        assert "<figcaption>Twoway</figcaption>" in divs[0].text
        assert "g1" in r.figures
        if "tabs" in bo:
            panels = {p.title: p for t in models if isinstance(t, Tabs)
                      for p in t.tabs}
            assert set(panels) == {"A", "B"}
            assert _image_divs(_models(panels["B"])) == divs
            assert _image_divs(_models(panels["A"])) == []


class TestTheServedApp:

    def test_same_div(self, tmp_path):
        sp, dp = _spec(tmp_path, layout="1 2")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = render_models(dr.DashRenderer(sp, dp))
        saved = _image_divs(_models(r._last_layout_root))
        doc, src = _served_doc(tmp_path, sp, dp)
        served = _image_divs([m for root in doc.roots
                              for m in root.references()])
        assert len(saved) == len(served) == 1
        assert served[0].text == saved[0].text
        assert '<a href="scatter.html">' in served[0].text
        assert served[0].html_attributes == saved[0].html_attributes
        for fn in ("_dash_image_html", "_dash_image_div",
                   "_dash_image_link_ok"):
            assert f"def {fn}(" in src, fn
        # The app reads no file: the embedded spec carries the address.
        assert "svg_truth_smoke" not in src
        assert "def _dash_image_check(" not in src


class TestNoImage:

    def test_spec_and_page_unchanged(self, tmp_path):
        sp, dp = _spec(tmp_path, images=False, layout="1 1")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = render_models(dr.DashRenderer(sp, dp))
        assert "images" not in r.master_spec
        assert r.image_divs == {}
        assert _image_divs(_models(r._last_layout_root)) == []
        capped = dr._dash_cap_spec({"graphs": [], "kpis": [],
                                    "build_options": {}}, dr._dash_limits({}))
        assert "images" not in capped
        doc, _ = _served_doc(tmp_path, sp, dp)
        assert _image_divs([m for root in doc.roots
                            for m in root.references()]) == []


class TestTheBound:

    def test_the_images_limit_keeps_the_first(self):
        ims = [{"name": f"im{i}", "uri": _URI} for i in range(1, 4)]
        spec = {"graphs": [], "kpis": [], "images": ims,
                "build_options": {"registry": "im1 im2 im3"}}
        lim = dr._dash_limits({"limits": {"images": 2}})
        assert lim["images"] == 2
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            out = dr._dash_cap_spec(spec, lim)
        assert [i["name"] for i in out["images"]] == ["im1", "im2"]
        assert any("3 image panels, more than the 2" in str(x.message)
                   for x in w), [str(x.message) for x in w]

    def test_an_image_named_like_a_graph_is_refused(self):
        spec = {"graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                            "plots": []}],
                "kpis": [], "images": [{"name": "g1", "uri": _URI},
                                       {"name": "a__b", "uri": _URI},
                                       {"name": "ok", "uri": _URI}],
                "build_options": {"registry": "g1 ok"}}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            out = dr._dash_cap_spec(spec, dr._dash_limits({}))
        assert [i["name"] for i in out["images"]] == ["ok"]
        assert len(out["graphs"]) == 1
        assert w, "the refused image names are said"


class TestTheHelp:

    def test_the_section_says_what_is_refused(self):
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            hlp = fh.read()
        start = hlp.index("{marker image}")
        sec = hlp[start:hlp.index("{marker ", start + 1)]
        for word in ("foreignObject", "link(", ".html", "$dash_max_images"):
            assert word in sec, word
        assert "10,000,000" not in sec and "10 MB" not in sec
        assert "{synopt:{cmd:$dash_max_images}}" in hlp
        assert "{cmd:dash image using}" in hlp
