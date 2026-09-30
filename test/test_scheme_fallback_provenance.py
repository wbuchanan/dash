"""What the last-resort scheme is, and what a served dashboard says about it.

``SchemeParser.fallback()`` is the last line of defence: it returns a usable
scheme without reading any file, so a render on an install whose scheme files
cannot be read ends in a dashboard rather than a traceback.  Two things about
it were not true.

1.  It does not mirror s2color, though it says it does
-------------------------------------------------------
Its comment reads "Mirrors s2color so the output stays recognisable."
Measured against ``SchemeParser("s2color")`` parsed from the shipped file:
23 properties against 118, and **12 public attributes differ** --
``draw_major_vgrid`` (True -> False), ``grid_line_width`` (1.5 -> 0.8),
``area_alpha`` and ``bar_alpha`` (1.0 -> 0.8), ``heading_font_size``
(14pt -> 13pt), ``text_font_size`` (11pt -> 10pt), ``note_font_size``
(8pt -> 9pt), ``symbolsize`` ('medium' -> ''), ``graphsize_x``/``graphsize_y``
and ``legend_cols``/``legend_position`` (values -> None).

"Recognisable" is the whole justification for having a fallback at all, so
these tests hold it to its own claim rather than to a weaker one.  They
compare *attributes*, not the raw property dict: the fallback is written in
Stata colour names and s2color's file in resolved hex, so the dicts cannot be
compared directly and it is the translated values that reach a figure.

2.  A served dashboard built on the fallback said nothing
----------------------------------------------------------
``ServerAppBuilder`` bakes the parent's parsed properties into the generated
app and rebuilds a ``SchemeParser`` from them with ``_s.is_fallback = False``
written literally.  The standalone path warns at resolution time, in the
parent, so the *builder's* user is told.  Nobody who later runs the generated
app is: it is byte-indistinguishable in provenance from an app built on a
healthy install, and ``is_fallback`` has no reader anywhere in dash -- ``grep
-rn is_fallback`` over ``dash.ado``, ``dash_parse.mata``, ``scripts/`` and
``test/`` returned nothing before this file.

So the hardcoded ``False`` is not itself the defect: correcting it to ``True``
would change nothing observable.  The defect is that the app is silent, and
the fix is a notice the app emits, naming the scheme that was *requested* --
not ``self.scheme.name``, which is provably the literal ``"s2color"`` whenever
``is_fallback`` is true, and so would tell the user they asked for the thing
they got.

Tests: FBP-01 through FBP-12.  FBP-10..12 run the generated app; the source
checks FBP-05..07 alone passed with the notice deleted (WP-24).
"""
from __future__ import annotations

import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402

#: Attributes whose value is provenance, not style -- excluded from the
#: mirroring comparison because they are *meant* to differ.
PROVENANCE_ATTRS = frozenset({"is_fallback"})


def _public_attrs(scheme):
    out = {}
    for name in dir(scheme):
        if name.startswith("_") or name in PROVENANCE_ATTRS:
            continue
        try:
            value = getattr(scheme, name)
        except Exception:                                  # pragma: no cover
            continue
        if callable(value):
            continue
        out[name] = value
    return out


# ==========================================================================
# FBP-01..04 — the fallback keeps the promise its comment makes
# ==========================================================================

class TestTheFallbackMirrorsS2color:

    def test_every_style_attribute_matches(self):
        """FBP-01. The claim, asserted whole.

        Twelve attributes differed when this was written.  Listing them
        individually would let the next one through.
        """
        real = _public_attrs(dr.SchemeParser("s2color"))
        fake = _public_attrs(dr.SchemeParser.fallback())
        assert set(real) == set(fake), (
            "the two schemes do not even expose the same attributes: "
            "%r" % (set(real) ^ set(fake),)
        )
        differing = {k: (real[k], fake[k]) for k in real if real[k] != fake[k]}
        assert not differing, (
            "SchemeParser.fallback() claims to mirror s2color but differs on "
            "%d attribute(s): %s"
            % (len(differing),
               ", ".join("%s (s2color=%r, fallback=%r)" % (k, a, b)
                         for k, (a, b) in sorted(differing.items())))
        )

    def test_it_still_reports_its_name_as_s2color(self):
        """FBP-02. The name is what it renders as; is_fallback is how it got there."""
        assert dr.SchemeParser.fallback().name == "s2color"

    def test_it_still_reports_that_it_is_a_fallback(self):
        """FBP-03. Mirroring s2color must not erase the provenance."""
        assert dr.SchemeParser.fallback().is_fallback is True
        assert dr.SchemeParser("s2color").is_fallback is False

    def test_it_needs_no_file(self):
        """FBP-04. The one thing the fallback exists for.

        Asserted by watching ``open``: a fallback that reached the disk would
        be useless on the install it is meant to rescue.
        """
        import builtins
        opened = []
        real_open = builtins.open

        def spy(path, *args, **kwargs):
            opened.append(str(path))
            return real_open(path, *args, **kwargs)

        builtins.open = spy
        try:
            scheme = dr.SchemeParser.fallback()
            scheme.default_color(0, "scatter")
        finally:
            builtins.open = real_open
        assert not [p for p in opened if p.endswith(".scheme")], (
            "fallback() read scheme file(s): %r" % (opened,)
        )
        # Positive control: the same spy must SEE the parser read a file.
        # An empty list proves nothing if the parser stops reading through
        # builtins.open -- io.open, for one, is bound to the original
        # function and bypasses the spy -- and a fallback that read
        # s2color.scheme that way passed the absence above (measured
        # 24sep2026).
        opened.clear()
        builtins.open = spy
        try:
            dr.SchemeParser("s2color")
        finally:
            builtins.open = real_open
        assert [p for p in opened
                if os.path.basename(p) == "dash-s2color.scheme"], (
            "the open() spy saw no read of dash-s2color.scheme while the parser "
            "parsed it, so its silence about fallback() means nothing: %r"
            % (opened,)
        )


# ==========================================================================
# FBP-05..09 — a served app says how it was built
# ==========================================================================

def _server_source(tmp_path, scheme_name, break_schemes):
    """Build a Bokeh-server app source and return it as text.

    When *break_schemes* is set, the scheme search directories are pointed at
    an empty directory so resolution genuinely falls back -- the state a
    net-installed dash was in for every scheme it shipped.
    """
    spec = {
        "build_options": {"layout": "1 1", "level": "95", "formats": {},
                          "scheme": scheme_name, "title": "T"},
        "graphs": [{
            "name": "g1",
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x",
                       "options": {}, "if_expr": "", "in_expr": ""}],
            "graph_options": {"name": "g1"}, "if_expr": "", "in_expr": "",
        }],
        "kpis": [],
    }
    data = {
        "values": [{"x": 1.0, "y": 2.0}, {"x": 2.0, "y": 3.0}],
        "variableLabels": {}, "valueLabels": {}, "valueLabelNames": {},
        "variableTypeIsString": {"x": False, "y": False},
    }
    spec_path = tmp_path / "spec.json"
    data_path = tmp_path / "data.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    data_path.write_text(json.dumps(data), encoding="utf-8")

    empty = tmp_path / "empty"
    empty.mkdir(exist_ok=True)
    app_path = tmp_path / "app.py"

    saved_dirs = dr.SchemeParser._SCHEME_SEARCH_DIRS
    saved_root = dr.SchemeParser._PLUS_ROOT
    if break_schemes:
        dr.SchemeParser._SCHEME_SEARCH_DIRS = (str(empty),)
        dr.SchemeParser._PLUS_ROOT = None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(str(spec_path), str(data_path)).build(
                str(app_path))
    finally:
        dr.SchemeParser._SCHEME_SEARCH_DIRS = saved_dirs
        dr.SchemeParser._PLUS_ROOT = saved_root
    return app_path.read_text(encoding="utf-8")


def _run_app_scheme(source):
    """Run a generated app's own scheme set-up; return (scheme, warnings).

    Executes the app's top-level statements up to, not including,
    ``_DASH_SCHEME = _dash_build_scheme()`` -- its imports, constants, the
    class sources, the baked-in properties and the fallback notice -- and
    then calls the app's ``_dash_build_scheme()``.  Nothing past that line
    runs, so no document or server is touched.  The notice is written into
    EVERY app and switched on at run time by ``_DASH_SCHEME_IS_FALLBACK``,
    so only running it tells a healthy app from a fallback one; a text
    search of the source cannot.
    """
    import ast
    tree = ast.parse(source)
    stop = [i for i, node in enumerate(tree.body)
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "_DASH_SCHEME"
                    for t in node.targets)]
    assert len(stop) == 1, "the app no longer builds _DASH_SCHEME once"
    prefix = ast.Module(body=tree.body[:stop[0]], type_ignores=[])
    namespace = {"__name__": "dash_generated_app_prefix"}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exec(compile(prefix, "generated_app.py", "exec"), namespace)
        scheme = namespace["_dash_build_scheme"]()
    return scheme, [str(w.message) for w in caught]


class TestAServedAppReportsHowItWasBuilt:

    def test_an_app_built_on_a_fallback_carries_a_notice(self, tmp_path):
        """FBP-05. Measured before: zero warnings at import, provenance lost.

        This asserts the RECORD.  That the app acts on it is FBP-10, which
        runs the app: a text search for ``warn(`` here passed with the
        notice deleted (WP-24), because every generated app carries 64
        other ``warn(`` calls in the source it copies from the renderer.
        """
        source = _server_source(tmp_path, "economist", break_schemes=True)
        assert "_DASH_SCHEME_IS_FALLBACK = True" in source, (
            "the generated app does not record that it was built on the "
            "fallback scheme"
        )

    def test_the_notice_names_the_scheme_that_was_asked_for(self, tmp_path):
        """FBP-06. ``self.scheme.name`` is 's2color' whenever is_fallback is
        true, so a message built from it tells the user they got what they
        asked for. The REQUESTED name is what has to appear.

        The app must carry the requested name as its own value.  This
        asserted only that "economist" occurs somewhere in the source, which
        every generated app satisfies thirteen times over -- the copied
        SchemeParser lists the built-in names -- so it passed with the notice
        naming s2color instead (WP-24).  FBP-10 reads the notice itself.
        """
        source = _server_source(tmp_path, "economist", break_schemes=True)
        assert "_DASH_SCHEME_REQUESTED = 'economist'" in source, (
            "the app does not record the scheme that was asked for, so its "
            "notice cannot tell the user what they did not get"
        )

    def test_a_healthy_app_carries_no_notice(self, tmp_path):
        """FBP-07. The note must be silent on a working install.

        The record says so here; FBP-12 runs the app and hears nothing.
        (This also asserted that "could not be read" was absent from the
        source, a phrase the notice does not contain, so it could not fail.)
        """
        source = _server_source(tmp_path, "economist", break_schemes=False)
        assert "_DASH_SCHEME_IS_FALLBACK = False" in source

    def test_the_rebuilt_scheme_does_not_misreport_its_provenance(self,
                                                                  tmp_path):
        """FBP-08. ``_s.is_fallback = False`` was written literally.

        The scheme the app rebuilds, run, says it IS the fallback, and the
        app still draws.  This asserted only that the literal line was
        absent, which any other spelling of the same bug passes (WP-24).
        """
        from bokeh.document import Document
        source = _server_source(tmp_path, "economist", break_schemes=True)
        assert _CURDOC_ATTACH in source, "the generated app's curdoc attach moved"
        ns = {"__name__": "dash_fbp_app_rebuilt"}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            exec(compile(source.replace(_CURDOC_ATTACH, "pass"),
                         "dash_fbp_app_rebuilt.py", "exec"), ns)
        assert ns["_DASH_SCHEME"].is_fallback is True, (
            "the app's scheme reports a healthy provenance although the "
            "build fell back"
        )
        doc = Document()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ns["make_document"](doc)
        assert doc.roots, "an app built on the fallback drew nothing"
        # The control: a healthy build's scheme says it did not fall back,
        # and is the scheme asked for.  Dropping the assignment altogether
        # passed the literal's absence (measured 24sep2026).
        healthy = _server_source(tmp_path, "economist",
                                 break_schemes=False)
        scheme, _ = _run_app_scheme(healthy)
        assert scheme.is_fallback is False
        assert scheme.name == "economist"

    def test_the_generated_app_still_parses(self, tmp_path):
        """FBP-09. A notice that breaks the app is worse than no notice.

        Parsed, and read: the provenance flag is the real assignment, with
        the value the build had, and the entry point bokeh serve calls is
        still defined -- not just any text Python accepts.
        """
        import ast
        for broken in (True, False):
            source = _server_source(tmp_path, "economist",
                                    break_schemes=broken)
            tree = ast.parse(source)
            flags = [node.value.value for node in tree.body
                     if isinstance(node, ast.Assign)
                     and [getattr(t, "id", None) for t in node.targets]
                     == ["_DASH_SCHEME_IS_FALLBACK"]
                     and isinstance(node.value, ast.Constant)]
            assert flags == [broken], flags
            assert "make_document" in {
                node.name for node in tree.body
                if isinstance(node, ast.FunctionDef)}


# ==========================================================================
# FBP-10..12 -- the served app, RUN: what whoever starts it is told
# ==========================================================================
#
# FBP-05..07 read the generated source, and three of their string checks
# could not fail: ``warn(`` and ``economist`` occur in every generated app
# (64 and 13 times over, in the renderer source it copies), and "could not
# be read" is not in the notice at all.  Measured under WP-24: with the
# notice deleted, and with the notice naming s2color instead of the scheme
# asked for, FBP-01..09 all passed.  These run the app, as `python app.py'
# or `bokeh serve' would import it, and listen.

#: The generated app's own attach line, replaced so running it does not
#: add a document to Bokeh's process-global curdoc().
_CURDOC_ATTACH = "if __name__ != '__main__':\n    make_document(curdoc())"

#: The words the notice opens with.
_NOTICE = "this app was built where no .scheme file could be read"


def _notices_when_run(source, tag):
    """Run the app's module code and return the fallback notices it raised."""
    assert _CURDOC_ATTACH in source, "the generated app's curdoc attach moved"
    ns = {"__name__": "dash_fbp_app_%s" % tag}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exec(compile(source.replace(_CURDOC_ATTACH, "pass"),
                     "dash_fbp_app_%s.py" % tag, "exec"), ns)
    return [str(w.message) for w in caught
            if issubclass(w.category, UserWarning) and _NOTICE in str(w.message)]


class TestAServedAppSaysSoWhenItRuns:

    def test_an_app_built_on_the_fallback_warns_once_when_it_runs(
            self, tmp_path):
        """FBP-10. The provenance is acted on, not merely recorded."""
        source = _server_source(tmp_path, "economist", break_schemes=True)
        notices = _notices_when_run(source, "fallback")
        assert len(notices) == 1, (
            "an app built where no .scheme file could be read raised %d "
            "fallback notice(s) when run, not one: %r" % (len(notices), notices)
        )
        assert "You asked for economist" in notices[0], (
            "the notice does not name the scheme that was asked for: %r"
            % (notices[0],)
        )

    def test_the_notice_does_not_say_the_fallback_was_asked_for(self,
                                                                tmp_path):
        """FBP-11. The fallback is named s2color, so a notice built from the
        drawn scheme's name would tell the user they got what they asked for."""
        source = _server_source(tmp_path, "economist", break_schemes=True)
        for notice in _notices_when_run(source, "fallback_name"):
            assert "You asked for s2color" not in notice, notice

    def test_a_healthy_app_says_nothing_when_it_runs(self, tmp_path):
        """FBP-12. The notice is for a broken build only."""
        source = _server_source(tmp_path, "economist", break_schemes=False)
        assert _notices_when_run(source, "healthy") == [], (
            "an app built on the real economist scheme raised the fallback "
            "notice when run"
        )
