"""Three input surfaces that did not hold, found by an adversarial pass.

1. `dash serve` bound every interface. The generated launcher's own
   `--address` help says "(default: loopback)", but the default was None,
   which Bokeh reads as "bind everything". Measured: the listening sockets
   were ('0.0.0.0', port) and ('::', port), reachable from the LAN. The only
   gate was `allow_websocket_origin`, which filters a CLIENT-SUPPLIED header:
   a non-browser client that sends no Origin, or forges
   `Origin: http://localhost:<port>`, completed the handshake. dash.sthlp
   told the user the connection was restricted to loopback. The help file
   also says the generated app embeds the whole dataset.

2. `translate_mcolor` passed any 4- or 7-character string beginning with `#`
   through as a colour, without checking it was hex. `SchemeParser` puts that
   value into a `<style>` block, where `html.escape` leaves `{`, `}` and `;`
   alone -- so a .scheme file, which dash.sthlp invites the user to take from
   the working directory, could close dash's own CSS rule and open its own.
   The KPI colour path was hardened against exactly this; this was the one
   colour path left without the check.

3. `_stata_if_to_pandas` rewrote `!`, `~=`, `inlist()` and `missing()`
   everywhere, including inside quoted string literals, so

       dash scatter price weight if make == "Wow!"

   filtered on "Wow~", matched nothing and drew an empty graph without a
   word. Its sibling `_stata_expr_to_python` tracks quote state precisely and
   its docstring says why; this one did not.
"""
import math
import os
import re
import socket
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr


# ---------------------------------------------------------------------------
# 1. The served socket
# ---------------------------------------------------------------------------

class TestServeBindsLoopbackByDefault:
    @staticmethod
    def _app_source(tmp_path):
        """The real artefact: the .py a user is told to keep and re-run."""
        import json
        import warnings
        import pandas as pd
        sys.path.insert(0, _HERE)
        from conftest import make_data_json
        sp = tmp_path / "s.json"
        dp = tmp_path / "d.json"
        sp.write_text(json.dumps({
            "graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "options": {},
                        "plots": [{"type": "scatter", "yvar": "y",
                                   "xvar": "x", "options": {}}]}],
            "kpis": [],
            "build_options": {"layout": "auto", "registry": "g1",
                              "level": "95", "formats": {}, "theme": "",
                              "scheme": "", "session_scheme": ""}}))
        dp.write_text(json.dumps(make_data_json(
            pd.DataFrame({"x": [1.0, 2.0], "y": [3.0, 4.0]}))))
        ap = tmp_path / "app.py"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
        return ap.read_text()

    def test_the_generated_app_binds_loopback_by_default(self, tmp_path):
        src = self._app_source(tmp_path)
        m = re.search(r"_kw = \{'address':([^}]*)\}", src)
        assert m, (
            "the address kwarg is no longer built where this looks for it, "
            "so this check would go blind"
        )
        assert "127.0.0.1" in m.group(1), (
            "the generated launcher passes no address unless one is given, "
            "so Bokeh binds every interface -- while --address's own help "
            "text says the default is loopback"
        )

    def test_an_operator_can_still_open_it_deliberately(self, tmp_path):
        """--address must still win, or the fix breaks a real deployment."""
        src = self._app_source(tmp_path)
        assert "address or '127.0.0.1'" in src, (
            "the address argument no longer overrides the default"
        )

    def test_the_help_does_not_claim_an_access_control_it_has_not_got(self):
        """dash.sthlp said WebSocket origin checking restricts to loopback."""
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            h = fh.read()
        i = h.index("{marker server_mode}")
        j = h.index("{marker examples}", i)
        # SMCL wraps a sentence over several lines, so the claim has to be
        # searched for with the line breaks collapsed. Searching the raw text
        # found nothing and passed while the claim was still there.
        sec = re.sub(r"\s+", " ", h[i:j])
        assert "restricts WebSocket connections to the loopback interface" \
            not in sec, (
            "the help states the Origin allow-list restricts connections to "
            "loopback. It filters a header the client supplies, and a client "
            "that omits the header is admitted."
        )


# ---------------------------------------------------------------------------
# 2. Colour reaching CSS
# ---------------------------------------------------------------------------

class TestAColourMustBeAColour:
    @pytest.mark.parametrize("bad", [
        "#}a{b;c", "#%d{e;f", '#x"y<z>', "#a;b;c", "#12 45", "#{}{}{}",
        "#zzz", "#gggggg",
    ])
    def test_a_non_hex_hash_string_is_rejected(self, bad):
        tr = dr.OptionTranslator()
        with pytest.raises(ValueError):
            tr.translate_mcolor(bad)

    @pytest.mark.parametrize("good", [
        "#fff", "#FFF", "#1a476f", "#1A476F", "#000000", "#abc",
    ])
    def test_real_hex_still_passes(self, good):
        # The translator lower-cases what it returns, so compare that way.
        assert dr.OptionTranslator().translate_mcolor(good) == good.lower()

    def test_a_scheme_cannot_break_out_of_its_css_rule(self, tmp_path,
                                                       monkeypatch):
        """The end-to-end shape of the attack, through a .scheme file.

        The file goes in the working directory because that is where
        dash.sthlp tells the user to put a custom scheme, and because the
        path validator -- correctly -- refuses to read one from anywhere
        else.
        """
        monkeypatch.chdir(tmp_path)
        p = tmp_path / "evil.scheme"
        p.write_text(
            "color background #}a{b;c\n"
            "color heading #%d{e;f\n"
            "color legend #000000\n"
        )
        css = dr.SchemeParser("evil").css_style_element()
        body = re.search(r"body \{([^}]*)\}", css)
        assert body, "the body rule is no longer in the stylesheet"
        assert "{" not in body.group(1), (
            f"a scheme value closed dash's own CSS rule: {body.group(1)!r}"
        )
        # And nothing outside the known rules is emitted.
        assert css.count("{") == css.count("}")


# ---------------------------------------------------------------------------
# 3. A quoted string is data, not syntax
# ---------------------------------------------------------------------------

class TestIfQualifierLeavesStringLiteralsAlone:
    @pytest.mark.parametrize("expr", [
        'make == "Wow!"',
        "make == 'Wow!'",
        'make == "a~=b"',
        'make != "x!"',
        'make == "inlist(a,b)"',
        'make == "missing(z)"',
        'make == "inrange(1,2)"',
        'name == "O\'Neill"'.replace("\\'", "'"),
    ])
    def test_the_literal_is_unchanged(self, expr):
        out = dr._stata_if_to_pandas(expr)
        for lit in re.findall(r'"([^"]*)"|\'([^\']*)\'', expr):
            text = lit[0] or lit[1]
            if text:
                assert text in out, (
                    f"the qualifier {expr!r} was rewritten to {out!r}; the "
                    f"string literal {text!r} no longer appears, so it "
                    f"filters on something the user did not write"
                )

    def test_the_translation_still_happens_outside_quotes(self):
        """The control: the rewriting these tests protect must still work."""
        assert "!=" in dr._stata_if_to_pandas("rep78 ~= 3")
        assert "~" in dr._stata_if_to_pandas("!foreign")
        out = dr._stata_if_to_pandas("inlist(rep78, 1, 2)")
        assert "inlist" not in out and "==" in out
        out = dr._stata_if_to_pandas("missing(rep78)")
        assert "missing(" not in out

    def test_a_mixed_expression_rewrites_only_the_code(self):
        out = dr._stata_if_to_pandas('make == "Wow!" & rep78 ~= 3')
        assert '"Wow!"' in out, f"literal mangled: {out!r}"
        assert "!=" in out.split('"Wow!"')[1], f"code not rewritten: {out!r}"


# ===========================================================================
# WP-20 · TR-20.5 -- pin the defences that are already correct and verified.
#
# Six defences guard the surfaces `dash' opens with untrusted input: the
# `function' expression whitelist, the `if' qualifier whitelist, the scheme
# file containment, the two CSS-colour sanitisers, FilterBuilder._safe, and
# the served app's loopback binding.  This block pins each so a later edit
# cannot loosen it in silence.  Each defence is pinned in BOTH render modes
# wherever the served app has its own path: the generated .py copies
# GlyphMapper, the qualifier/colour helpers and the launcher BY SOURCE, so
# the honest check of the served side is to build that .py and run it.
#
# One pin found a real gap and is reported in the class that closes it
# (TestTheFunctionExpressionWhitelist): the AST `Constant' branch accepted
# ANY literal, so a str/bytes constant reached eval() and a power tower of
# bool constants bypassed the float coercion and hung the render.  Fixed in
# dash_render.py map_function's _validate_expr_node (the numeric-only guard).
# ===========================================================================

import importlib.util  # noqa: E402
import itertools  # noqa: E402
import json  # noqa: E402
import time  # noqa: E402
import warnings  # noqa: E402

_APP_SEQ = itertools.count(1)


def _sec_spec(plots, kpis=None, if_expr="", build=None):
    """A one-graph master spec, shaped as dash.ado writes one."""
    bo = {"layout": "auto", "registry": "g1", "level": "95",
          "formats": {}, "theme": "", "scheme": "", "session_scheme": ""}
    if build:
        bo.update(build)
    return {"graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "options": {}, "if_expr": if_expr, "in_expr": "",
                        "plots": plots}],
            "kpis": kpis or [], "build_options": bo}


def _sec_df():
    import pandas as pd
    return pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": [4.0, 5.0, 6.0]})


def _build_served_module(tmp_path, spec, df):
    """Build the generated server app for *spec* and return its module.

    The module is executed, which is itself a server-mode run: the emitted
    file ends with ``if __name__ != '__main__': make_document(curdoc())``, so
    importing it draws the whole dashboard once against Bokeh's current
    document.  A payload that executes therefore fires at import, before any
    assertion -- which is exactly what the file-marker pins rely on.
    """
    from conftest import make_data_json
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    tag = next(_APP_SEQ)
    sp = tmp_path / f"sec_s_{tag}.json"
    dp = tmp_path / f"sec_d_{tag}.json"
    ap = tmp_path / f"sec_a_{tag}.py"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(df)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
        ms = importlib.util.spec_from_file_location(f"_sec_app_{tag}", str(ap))
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
    return mod


def _served_function_points(mod):
    """The x_fn values the served document actually drew, if any."""
    from bokeh.document import Document
    from bokeh.models import ColumnDataSource
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        doc = Document()
        mod.make_document(doc)
    drew = 0
    for m in doc.select({"type": ColumnDataSource}):
        if "x_fn" in m.data:
            drew += len(m.data["x_fn"])
    return drew


# ---------------------------------------------------------------------------
# 4. The `function' expression AST whitelist
# ---------------------------------------------------------------------------

class TestTheFunctionExpressionWhitelist:
    """`twoway function y = <expr>' evaluates a user string.

    map_function rewrites Stata's ``^``, parses the result to an AST, walks it
    against a whitelist -- only ``x``/``pi``/``e``, a fixed set of maths
    functions, arithmetic operators and REAL numeric literals -- coerces
    integer literals to float (so ``9^9^9^9`` is ``inf``, not an exact
    bignum), and only then ``eval``\\ s with ``{'__builtins__': {}}``.  Both
    render modes run this one method: the served app copies GlyphMapper by
    source.  Anything the walk rejects must draw an empty line and reach
    neither ``compile`` nor ``eval``.

    GAP FOUND AND FIXED.  The ``Constant`` branch was ``pass  # numeric
    literals are always safe``, but it accepted EVERY literal.  A ``str``/
    ``bytes`` constant reached ``eval`` (``'%50000000d' % 1`` allocates 50 MB),
    and a power tower of ``bool`` constants -- ``(True+True)**(True+True+True)
    **...`` -- was computed exactly, because ``_floats_only`` coerces ``int``
    but deliberately skips ``bool``, so it held the GIL past 15 s the way the
    integer tower used to.  Fixed in ``_validate_expr_node`` (dash_render.py):
    the branch now accepts only real ``int``/``float`` and refuses ``bool``,
    ``str``, ``bytes``, ``complex``, ``None`` and ``Ellipsis``.
    """

    # Every construct the whitelist must refuse.  None may reach eval.
    _REFUSED = [
        # attribute access
        "x.__class__", "(1).__class__.__bases__", "x.real",
        # dunder names (as bare names, too)
        "__class__", "__import__", "__builtins__",
        # subscripts
        "x[0]", "x[0:1]", "x[::2]",
        # lambda
        "lambda: x", "(lambda: x)()",
        # comprehensions and generators
        "[c for c in (1,)]", "{c for c in (1,)}",
        "{c: c for c in (1,)}", "(c for c in (1,))",
        "abs(c for c in (1,))",
        # a call to any non-whitelisted name
        "open('/tmp/x')", "exec('1')", "eval('1')", "__import__('os')",
        "getattr(x, 'real')", "globals()",
        # starred arguments
        "sin(*x)", "sin(*[x])",
        # walrus
        "(w := x)", "sin(w := x)",
        # f-strings / JoinedStr
        "f'{x}'", "f'{sin(x)}'",
        # str and bytes constants are NOT numeric literals (the gap above)
        "'abc'", "b'abc'", "x + 'a'", "'%50000000d' % 1", "'a' * x",
        # and neither are bool / None / complex / Ellipsis
        "True", "False", "None", "1j", "x * 1j", "...",
    ]

    @staticmethod
    def _draw_with_eval_spy(expr, mapper=None):
        """Draw *expr* and report ``(eval_was_called, n_points)``.

        ``eval`` is a module global inside ``map_function``; shadowing
        ``dr.eval`` records whether execution was reached at all -- the
        strongest "nothing ran" proof for a payload with no file side effect.
        """
        from bokeh.plotting import figure
        import builtins
        calls = []
        real_eval = builtins.eval
        gm = mapper or dr.GlyphMapper()
        saved = getattr(dr, "eval", real_eval)
        dr.eval = lambda *a, **k: (calls.append(1), real_eval(*a, **k))[1]
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r = gm.map_function(figure(), expr, (0.0, 1.0), 5, {})
        finally:
            dr.eval = saved
        return bool(calls), len(r[0].data_source.data["x_fn"])

    @pytest.mark.parametrize("expr", _REFUSED)
    def test_the_shared_validator_refuses_and_never_evaluates(self, expr):
        called, n = self._draw_with_eval_spy(expr)
        assert not called, f"{expr!r} reached eval()"
        assert n == 0, f"{expr!r} drew {n} points; it should have been refused"

    @pytest.mark.parametrize("expr", [
        "x.__class__", "x[0]", "lambda: x", "[c for c in (1,)]",
        "__import__('os')", "sin(*x)", "(w := x)", "f'{x}'", "'abc'", "True",
    ])
    def test_the_served_app_refuses_the_same_constructs(self, tmp_path, expr):
        """The served path is the SAME map_function, copied by source."""
        mod = _build_served_module(
            tmp_path,
            _sec_spec([{"type": "scatter", "yvar": "y", "xvar": "x",
                        "options": {}},
                       {"type": "function", "expr": expr, "options": {}}]),
            _sec_df())
        assert _served_function_points(mod) == 0, (
            f"the served app evaluated {expr!r}"
        )

    # An observable side effect: reaching `open' through object.__subclasses__
    # -- the standard escape from a namespace whose __builtins__ is empty --
    # would write this file.  It is an attribute+subscript+call chain, refused
    # at validation, so the file must never appear in EITHER mode.
    _ESCAPE = (
        "[c for c in ().__class__.__bases__[0].__subclasses__() "
        "if c.__name__ == '_wrap_close'][0].__init__.__globals__"
        "['__builtins__']['open'](%r, 'w').write('PWNED')"
    )

    def test_nothing_executes_standalone(self, tmp_path):
        from bokeh.plotting import figure
        marker = tmp_path / "FN_STANDALONE"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.GlyphMapper().map_function(
                figure(), self._ESCAPE % str(marker), (0.0, 1.0), 5, {})
        assert not marker.exists(), (
            f"a function expression wrote {marker}: the __subclasses__ escape "
            f"ran through the empty-builtins namespace"
        )

    def test_nothing_executes_served(self, tmp_path):
        marker = tmp_path / "FN_SERVED"
        # Building AND importing the app runs make_document(curdoc()) once;
        # if the expression executed, the marker would exist before we look.
        mod = _build_served_module(
            tmp_path,
            _sec_spec([{"type": "scatter", "yvar": "y", "xvar": "x",
                        "options": {}},
                       {"type": "function",
                        "expr": self._ESCAPE % str(marker), "options": {}}]),
            _sec_df())
        _served_function_points(mod)
        assert not marker.exists(), (
            f"the served app wrote {marker} from a function expression"
        )

    def test_a_bool_power_tower_draws_empty_and_does_not_hang(self):
        """The gap's resource half: bool constants must not defeat the float
        coercion that turns a power tower into ``inf``."""
        from bokeh.plotting import figure
        nine = "(" + "+".join(["True"] * 9) + ")"
        expr = f"{nine}^{nine}^{nine}"      # (True+..)^(True+..)^(True+..)
        started = time.time()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.GlyphMapper().map_function(figure(), expr, (0.0, 1.0), 5, {})
        assert time.time() - started < 5.0, (
            "a bool power tower held the interpreter; _floats_only skips bool, "
            "so the constant whitelist is what has to refuse it"
        )
        assert len(r[0].data_source.data["x_fn"]) == 0

    @pytest.mark.parametrize("expr", [
        "x", "x^2", "2*x^3 - 1", "sin(x)", "exp(-x) * cos(x)",
        "log(x + 1)", "sqrt(abs(x))", "2*pi*x", "3.14", "9^9^9^9",
    ])
    def test_ordinary_expressions_still_draw(self, expr):
        """The control: a numeric expression must survive the tighter guard.
        ``9^9^9^9`` is the one that draws nothing -- it overflows, as a
        float and never as an exact integer -- so the guard is not a blanket
        ban on powers.  It is missing in Stata, which twoway draws as
        nothing, in silence; so it is drawn at each x with every y missing.
        It was drawn as an empty layer and reported as one until the
        overflow was read as Stata's missing value
        (test_immediate_dashboards.py)."""
        from bokeh.plotting import figure
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.GlyphMapper().map_function(figure(), expr, (0.0, 1.0), 5, {})
        data = r[0].data_source.data
        n = len(data["x_fn"])
        assert n == 5, f"{expr!r} drew {n} points"
        missing = [not math.isfinite(float(v)) for v in data["y_fn"]]
        assert all(missing) if expr == "9^9^9^9" else not any(missing), (
            f"{expr!r} drew {list(data['y_fn'])}"
        )


# ---------------------------------------------------------------------------
# 5. The `if' qualifier whitelist
# ---------------------------------------------------------------------------

class TestTheIfQualifierWhitelist:
    """`if <expr>' selects rows through pandas' ``DataFrame.query``.

    ``_dash_qualified_frame`` -- the one path both modes use, and the one the
    served app copies by source -- translates Stata's idioms, then rejects the
    result unless ``_validate_if_expr``'s AST whitelist passes it: only column
    names, the safe bare names, comparisons and boolean/bitwise connectives.
    ``query(engine='python')`` resolves ``@name`` from the caller's scope and
    would run arbitrary Python, so ``@`` is hard-rejected before parsing and
    every Call/Attribute/Subscript/Lambda/comprehension is refused.  A
    rejected qualifier leaves the frame UNFILTERED and warns; it must never
    filter on something the user did not write, and never execute.
    """

    @staticmethod
    def _df():
        import pandas as pd
        return pd.DataFrame({"mpg": [10.0, 20.0, 30.0, 40.0],
                             "make": ["a", "b", "c", "d"]})

    # `@local' is listed on its own: DataFrame.query resolves @name from the
    # caller's frame, so this is the payload the @-ban exists for.  The rest
    # are the other constructs the whitelist must refuse.
    _REFUSED = [
        "@evil",
        "mpg > 1 & @evil",
        "__import__('os').system('true')",
        "mpg == open('/tmp/x')",
        "mpg.__class__",
        "mpg.values > 1",
        "abs(mpg) > 1",
        "len(mpg) > 0",
        "`mpg` > 1",
        "import os",
        "(lambda: True)()",
        "mpg == (lambda: 1)",
        "mpg[0] > 1",
        "(z := mpg) > 1",
        "f'{mpg}' == 'a'",
        "[c for c in mpg]",
    ]

    @pytest.mark.parametrize("expr", _REFUSED)
    def test_a_refused_qualifier_warns_and_filters_nothing(self, expr):
        df = self._df()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            out = dr._dash_qualified_frame(df, expr, "")
        assert len(out) == len(df), f"{expr!r} filtered the frame"
        assert any("if_expr filter skipped" in str(w.message) for w in caught), (
            f"{expr!r} was rejected in silence"
        )

    def test_the_at_reference_never_calls_the_object_it_names(self):
        """The @-ban is load-bearing: query would resolve @name from this
        module's scope and call it.  It must not."""
        fired = []
        dr._tr205_if_sentinel = lambda: fired.append(1) or True
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr._dash_qualified_frame(self._df(),
                                         "@_tr205_if_sentinel()", "")
        finally:
            del dr._tr205_if_sentinel
        assert not fired, (
            "an @-reference in an if qualifier executed a Python callable"
        )

    def test_a_string_closing_a_quote_early_is_data_not_syntax(self):
        """A literal that tries to break out of its own quotes stays one
        literal: it matches no row, and nothing is executed."""
        df = self._df()
        expr = 'make == "a\\" or @evil or \\"z"'
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            out = dr._dash_qualified_frame(df, expr, "")
        # Either it is one big string literal that matches nothing, or it is
        # refused and left unfiltered -- never a partial filter smuggling the
        # `@evil' out of the quotes.
        assert len(out) in (0, len(df)), (
            f"the early-quote-close was interpreted as syntax: {len(out)} rows"
        )

    def test_the_validator_stays_load_bearing(self):
        """The control: with the whitelist bypassed, the same payloads DO run
        -- so it is the validator, not luck, that stops them."""
        import pandas as pd
        marker = {}
        df = pd.DataFrame({"mpg": [1.0, 2.0]})
        dr._tr205_if_sentinel = lambda: marker.setdefault("hit", True) or True
        saved = dr._validate_if_expr
        dr._validate_if_expr = lambda e, c: True
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    dr._dash_qualified_frame(df, "@_tr205_if_sentinel()", "")
                except Exception:
                    pass
        finally:
            dr._validate_if_expr = saved
            del dr._tr205_if_sentinel
        assert marker.get("hit"), (
            "the payload did not run even with the validator disabled, so "
            "this control proves nothing about the validator"
        )

    def test_a_hostile_per_graph_if_does_not_execute_when_served(self, tmp_path):
        """The served app copies _dash_qualified_frame; a graph-level `if'
        with an injection must leave the dashboard intact and run nothing."""
        marker = tmp_path / "IF_SERVED"
        payload = "__import__('pathlib').Path(%r).touch() or mpg > 0" % str(marker)
        mod = _build_served_module(
            tmp_path,
            _sec_spec([{"type": "scatter", "yvar": "y", "xvar": "x",
                        "options": {}}], if_expr=payload),
            _sec_df())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from bokeh.document import Document
            mod.make_document(Document())
        assert not marker.exists(), "a served if qualifier executed"


# ---------------------------------------------------------------------------
# 6. Scheme file containment
# ---------------------------------------------------------------------------

class TestSchemeFileContainment:
    """`scheme()'/`theme()' and every ``#include`` name reach
    ``SchemeParser._resolve_path``, which is the only thing between that string
    and the filesystem.  A candidate is admitted only if BOTH its ``abspath``
    and its ``realpath`` lie inside an allowed directory -- the scheme search
    dirs and the working directory -- so ``../`` escapes, absolute paths,
    ``#include ../../x`` and a symlink pointing out are all refused, and none
    of them reads a byte outside those directories.
    """

    @staticmethod
    def _sandbox(tmp_path, monkeypatch):
        """Point SchemeParser at a search dir and a CWD we own, and return
        ``(search_dir, cwd, outside_dir)`` all realpath'd."""
        root = os.path.realpath(str(tmp_path))
        sdir = os.path.join(root, "schemes")
        cwd = os.path.join(root, "work")
        outside = os.path.join(root, "outside")
        for d in (sdir, cwd, outside):
            os.makedirs(d, exist_ok=True)
        with open(os.path.join(outside, "secret.scheme"), "w") as fh:
            fh.write("color background #abcdef\ncolor p1 forest_green\n")
        monkeypatch.setattr(dr.SchemeParser, "_SCHEME_SEARCH_DIRS", (sdir,))
        monkeypatch.setattr(dr.SchemeParser, "_PLUS_ROOT", None)
        monkeypatch.chdir(cwd)
        return sdir, cwd, outside

    @staticmethod
    def _open_spy(monkeypatch, allowed):
        """Record every file opened; return the list of reads OUTSIDE the
        allowed directories."""
        import builtins
        outside_reads = []
        real_open = builtins.open
        allowed = [os.path.realpath(a) for a in allowed]

        def spy(path, *a, **k):
            rp = os.path.realpath(str(path))
            if not any(rp == d or rp.startswith(d + os.sep) for d in allowed):
                outside_reads.append(rp)
            return real_open(path, *a, **k)

        monkeypatch.setattr(dr, "open", spy, raising=False)
        return outside_reads

    def test_a_relative_traversal_is_refused(self, tmp_path, monkeypatch):
        sdir, cwd, outside = self._sandbox(tmp_path, monkeypatch)
        reads = self._open_spy(monkeypatch, [sdir, cwd])
        for name in ("../outside/secret", "../outside/secret.scheme",
                     "../../outside/secret", "./../outside/secret"):
            with pytest.raises(ValueError):
                dr.SchemeParser(name)
            assert dr.SchemeParser.can_resolve(name) is False
        assert reads == [], f"a traversal read outside the sandbox: {reads}"

    def test_an_absolute_path_is_refused(self, tmp_path, monkeypatch):
        sdir, cwd, outside = self._sandbox(tmp_path, monkeypatch)
        reads = self._open_spy(monkeypatch, [sdir, cwd])
        secret = os.path.join(outside, "secret.scheme")
        for name in (secret, secret[:-len(".scheme")]):
            with pytest.raises(ValueError):
                dr.SchemeParser(name)
        assert reads == [], f"an absolute path read outside the sandbox: {reads}"

    def test_an_include_out_of_the_directory_is_not_read(self, tmp_path,
                                                         monkeypatch):
        sdir, cwd, outside = self._sandbox(tmp_path, monkeypatch)
        # A scheme that is itself legitimate but whose #include escapes.
        with open(os.path.join(sdir, "child.scheme"), "w") as fh:
            fh.write("#include ../../outside/secret\n"
                     "#include ../outside/secret.scheme\n"
                     "color p1 maroon\n")
        reads = self._open_spy(monkeypatch, [sdir, cwd])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sp = dr.SchemeParser("child")
        # The child parses; the escaping include is skipped, so the secret's
        # own property never lands and its file is never opened.  _props holds
        # the raw scheme tokens, not the translated hex.
        assert sp._props.get("color p1") == "maroon", "the child did not parse"
        assert sp._props.get("color background") != "#abcdef", (
            "an #include reached outside the scheme directory"
        )
        assert reads == [], f"an #include read outside the sandbox: {reads}"

    def test_a_symlink_pointing_out_is_refused(self, tmp_path, monkeypatch):
        sdir, cwd, outside = self._sandbox(tmp_path, monkeypatch)
        secret = os.path.join(outside, "secret.scheme")
        # A symlink INSIDE the search dir and one inside the CWD, each
        # pointing at a file outside both.
        os.symlink(secret, os.path.join(sdir, "evil.scheme"))
        os.symlink(secret, os.path.join(cwd, "cwdevil.scheme"))
        reads = self._open_spy(monkeypatch, [sdir, cwd])
        for name in ("evil", "evil.scheme", "cwdevil", "cwdevil.scheme"):
            with pytest.raises(ValueError, match="symlink"):
                dr.SchemeParser(name)
            assert dr.SchemeParser.can_resolve(name) is False
        assert reads == [], f"a symlink was followed out of the sandbox: {reads}"

    def test_a_scheme_that_really_is_inside_still_loads(self, tmp_path,
                                                        monkeypatch):
        """The control: containment must not refuse a legitimate file."""
        sdir, cwd, outside = self._sandbox(tmp_path, monkeypatch)
        with open(os.path.join(cwd, "mine.scheme"), "w") as fh:
            fh.write("color p1 navy\n")
        sp = dr.SchemeParser("mine")
        assert sp._props.get("color p1") == "navy"
        assert sp.p_colors[0] == "#1a476f"    # and it translates as navy does


# ---------------------------------------------------------------------------
# 7. The two CSS-colour sanitisers
# ---------------------------------------------------------------------------

class TestAColourNeverBreaksOutOfItsRule:
    """A KPI ``color()``/``bgcolor()`` lands inside ``style="...color:{c};"``,
    where ``html.escape`` does NOT stop a CSS property injection: ``;``, ``(``
    and ``)`` pass through.  ``_sanitize_css_color`` matches a value against
    one anchored regex -- hex, rgb/rgba, hsl/hsla, or a letters-only name --
    and returns the default otherwise; ``_resolve_kpi_color`` translates a
    Stata colour first and then sanitises.  The served app rebuilds the regex
    from the same source, so both modes agree.  None of these tricks may reach
    the document.
    """

    _DEFAULT = "#0a0b0c"
    _TRICKS = [
        "red\\3b background:url(x)",      # CSS-escaped semicolon
        "red\\;background:blue",
        "\\72\\65\\64",                    # 'red' written as CSS escapes
        "expression(alert(1))",           # legacy dynamic property
        "url(http://evil.example/x)",     # outbound request
        "url(",
        "javascript:alert(1)",
        "red\nbackground:url(x)",          # a newline splicing a declaration
        "red;\nbackground:blue",
        "red/**/;background:blue",         # a comment smuggling a property
        "r/**/ed",
        "red；background:url(x)",      # fullwidth semicolon U+FF1B
        "red；",
    ]

    @pytest.mark.parametrize("bad", _TRICKS)
    def test_the_sanitiser_returns_the_default(self, bad):
        # _resolve_kpi_color also NAMES an unrecognised colour; that note is
        # correct here and not what this test is about.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            assert dr._sanitize_css_color(bad, self._DEFAULT) == self._DEFAULT
            assert dr._resolve_kpi_color(bad, self._DEFAULT, "color") \
                == self._DEFAULT

    @pytest.mark.parametrize("bad", _TRICKS)
    def test_the_served_app_returns_the_default_too(self, tmp_path, bad):
        mod = getattr(self, "_mod", None)
        if mod is None:
            mod = _build_served_module(
                tmp_path,
                _sec_spec([{"type": "scatter", "yvar": "y", "xvar": "x",
                            "options": {}}]),
                _sec_df())
            type(self)._mod = mod
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            assert mod._sanitize_css_color(bad, self._DEFAULT) == self._DEFAULT
            assert mod._resolve_kpi_color(bad, self._DEFAULT, "color") \
                == self._DEFAULT

    def test_a_hostile_bgcolor_does_not_reach_the_rendered_card(self, tmp_path):
        """End to end: the payload must be absent from the saved HTML."""
        import pandas as pd
        sys.path.insert(0, os.path.join(_HERE, ".."))
        from conftest import make_data_json
        spec = _sec_spec(
            [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            kpis=[{"name": "k1", "stat": "mean", "var": "y", "fmt": "%9.1f",
                   "title": "T", "subtitle": "", "color": "",
                   "bgcolor": "red; background:url(http://evil.example/x)",
                   "update": "filter"}])
        sp = tmp_path / "css_s.json"
        dp = tmp_path / "css_d.json"
        sp.write_text(json.dumps(spec))
        dp.write_text(json.dumps(make_data_json(_sec_df())))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            html = dr.DashRenderer(str(sp), str(dp)).render()
        assert "evil.example" not in html, "a KPI bgcolor reached the document"

    @pytest.mark.parametrize("good,expect", [
        ("#1a476f", "#1a476f"), ("#FFF", "#fff"), ("red", "#ff0000"),
        ("navy", "#1a476f"), ("rgb(1,2,3)", "rgb(1,2,3)"),
        ("rebeccapurple", "rebeccapurple"),
    ])
    def test_a_real_colour_survives(self, good, expect):
        """The control: sanitising must not flatten a legitimate colour."""
        assert dr._resolve_kpi_color(good, self._DEFAULT, "color") == expect


# ---------------------------------------------------------------------------
# 8. FilterBuilder._safe
# ---------------------------------------------------------------------------

class TestFilterNamesCannotInjectScript:
    """A ``filter(varname)`` widget carries the variable's name into a Bokeh
    widget title.  ``FilterBuilder._safe`` HTML-escapes it (``quote=True``) so
    ``<``, ``>``, ``&`` and both quotes cannot open a tag or break an
    attribute, and the callback body is the fixed ``_FILTER_JS`` template --
    the name is never spliced into code.  Upstream, ``_dash_parse_filter_raw``
    (run by both modes) refuses any ``filter()`` whose variable is not a Stata
    name, so a hostile string never reaches a widget at all.
    """

    @pytest.mark.parametrize("hostile", [
        "<script>alert(1)</script>",
        '"><img src=x onerror=alert(1)>',
        "' onmouseover='x",
        "a&b",
    ])
    def test_safe_neutralises_the_html_active_characters(self, hostile):
        out = dr.FilterBuilder._safe(hostile)
        for ch in "<>\"'":
            assert ch not in out, f"{ch!r} survived escaping in {out!r}"
        assert "&" not in out.replace("&lt;", "").replace("&gt;", "") \
            .replace("&quot;", "").replace("&#x27;", "").replace("&amp;", ""), (
            f"a raw ampersand survived in {out!r}"
        )

    @pytest.mark.parametrize("legit", ["foreign", "rep78", "_x", "price_2020"])
    def test_a_legitimate_name_is_unchanged(self, legit):
        assert dr.FilterBuilder._safe(legit) == legit

    def test_a_hostile_name_is_escaped_in_the_widget_and_absent_from_code(self):
        from bokeh.models import ColumnDataSource
        hostile = '<img src=x onerror="alert(1)">'
        src = ColumnDataSource({hostile: [1.0, 2.0, 3.0]})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            widget, cb = dr.FilterBuilder.build_dropdown(
                hostile, src, label="", column=[1.0, 2.0, 3.0])
        assert hostile not in widget.title, (
            f"the raw name reached the widget title: {widget.title!r}"
        )
        assert "&lt;img" in widget.title, "the name was not escaped at all"
        assert hostile not in (cb.code or ""), (
            "the variable name was spliced into the callback code"
        )
        assert cb.code == dr._FILTER_JS, (
            "the callback body is no longer the fixed template"
        )

    def test_the_filter_parser_refuses_a_non_name_in_both_modes(self):
        """`_dash_parse_filter_raw' is the one parser both renderers run."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            specs = dr._dash_parse_filter_raw(
                "<script>alert(1)</script>, type(dropdown)")
        assert specs == [], "a non-name filter variable was accepted"
        assert any("is not a valid variable name" in str(w.message)
                   for w in caught), "the refusal was silent"


# ---------------------------------------------------------------------------
# 9. Loopback-by-default binding, at runtime in the generated app
# ---------------------------------------------------------------------------

class TestTheGeneratedAppBindsLoopbackAtRuntime:
    """``TestServeBindsLoopbackByDefault`` above pins the emitted SOURCE.  This
    pins the BEHAVIOUR: the generated app's own ``_dash_server_app()`` builds
    its Bokeh ``Server`` with ``address='127.0.0.1'`` when the operator gives
    no ``--address``, so ``dash serve`` on a laptop does not bind every
    interface.  The Server is inspected through a monkeypatched stand-in in the
    app's namespace; no server is ever started.
    """

    @staticmethod
    def _app_with_fake_server(tmp_path):
        mod = _build_served_module(
            tmp_path,
            _sec_spec([{"type": "scatter", "yvar": "y", "xvar": "x",
                        "options": {}}]),
            _sec_df())
        seen = []

        class _FakeServer:
            def __init__(self, *a, **k):
                seen.append(k)

            def start(self):
                raise AssertionError("the pin started a real server")

        mod.Server = _FakeServer
        return mod, seen

    def test_no_address_binds_loopback(self, tmp_path):
        mod, seen = self._app_with_fake_server(tmp_path)
        mod._dash_server_app()
        assert seen[-1].get("address") == "127.0.0.1", (
            f"the generated app bound {seen[-1].get('address')!r} with no "
            f"--address; Bokeh reads None as every interface"
        )

    def test_an_empty_address_still_binds_loopback(self, tmp_path):
        mod, seen = self._app_with_fake_server(tmp_path)
        mod._dash_server_app(address="")
        assert seen[-1].get("address") == "127.0.0.1"

    def test_an_operator_can_still_open_it_deliberately(self, tmp_path):
        mod, seen = self._app_with_fake_server(tmp_path)
        mod._dash_server_app(address="0.0.0.0")
        assert seen[-1].get("address") == "0.0.0.0", (
            "--address no longer overrides the loopback default"
        )


# ---------------------------------------------------------------------------
# User text is echoed as text (WP-20, P20-01..14 and P20-29)
# ---------------------------------------------------------------------------
_ADO = os.path.join(_HERE, "..", "dash.ado")
_MATA = os.path.join(_HERE, "..", "dash_parse.mata")
_SETUP = os.path.join(_HERE, "..", "dash_setup.ado")

# Locals that hold what the user typed, in the programs that echo them: an
# option value (_dash_validate_value's value and badvar), the plot-type
# token, a saving() path at every stage, port() and timeout(), link() and
# exclude() names, a weight expression, the unsupported-option list, a
# scatteri coordinate, and the raw build options.
_USER_TEXT_LOCALS = frozenset({
    "value", "badvar", "plottype", "fpath", "_base", "saving",
    "saving_path", "_sv", "port", "timeout", "lname", "ename", "_seg_wexp",
    "out", "yv", "layout", "link", "theme", "scheme", "fmt", "title",
    "subtitle", "tabs", "filter", "filterposition",
})


def _display_statements(path):
    """``(line number, statement)`` for every display statement, with its
    ``///`` continuation lines joined on."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        code = line.split("//", 1)[0] if not line.lstrip().startswith("//") else ""
        if re.match(r"\s*(?:noi(?:sily)?\s+)?di(?:s|sp|spl|spla|splay)?\b", code):
            start = i + 1
            stmt = line
            while stmt.rstrip().endswith("///") and i + 1 < len(lines):
                i += 1
                stmt = stmt.rstrip()[:-3] + " " + lines[i].strip()
            out.append((start, stmt))
        i += 1
    return out


class TestUserTextIsEchoedAsText:
    """``display`` reads its text as SMCL, and a macro expanded into a display
    line is parsed with it: an echoed ``{bf:X}`` printed a bold X, ``{stata
    ...}`` drew a link a click runs, and a double quote in a value ended the
    string so what followed ran as display directives (P9-11..14; measured
    at e932446, ``saving(`"p" _dup(3) "INJ.gph"')`` printed INJ.html three
    times).  Every echo of the user's text now goes through the Mata helper
    ``_dash_say``, which reads the text by value and shows it as written.
    These pins keep a new ``display`` from expanding it again."""

    def test_no_display_line_expands_user_text(self):
        bad = []
        for n, stmt in _display_statements(_ADO):
            names = set(re.findall(
                r"`(?:macval\()?([A-Za-z_][A-Za-z0-9_]*)\)?'", stmt))
            hit = sorted(names & _USER_TEXT_LOCALS)
            if hit:
                bad.append(f"dash.ado:{n} expands {hit}")
        assert not bad, "\n".join(bad)

    def test_the_detector_sees_a_display_that_expands_user_text(self, tmp_path):
        f = tmp_path / "probe.ado"
        f.write_text('program define p\n'
                     '    display as error "got: `value\'"\n'
                     '    di as text `"a"\' ///\n'
                     '        `"`macval(saving)\'"\'\n'
                     '    display as text "fine: `_safe\'"\n'
                     'end\n', encoding="utf-8")
        found = {n: set(re.findall(
            r"`(?:macval\()?([A-Za-z_][A-Za-z0-9_]*)\)?'", s))
            for n, s in _display_statements(str(f))}
        assert found[2] == {"value"}
        assert found[3] == {"saving"}
        assert found[5] == {"_safe"}

    def test_the_echo_helper_is_in_the_library_dash_requires(self):
        with open(_MATA, encoding="utf-8") as fh:
            mata = fh.read()
        with open(_ADO, encoding="utf-8") as fh:
            ado = fh.read()
        for fn in ("_dash_say", "_dash_is_digits", "_dash_layout_cells",
                   "_dash_layout_refusal"):
            assert re.search(r"^\S.*\b%s\(" % fn, mata, re.M), fn
            block = ado[ado.index("local _needed"):ado.index("quietly capture mata: mata describe _dash_check_utf8()")]
            assert fn in block, f"{fn} is not in _dash_require_mata's list"

    def test_port_and_timeout_are_not_proven_by_a_regex(self):
        """StataNow's regexm() matches ^[0-9]+$ against "7" + char(10)."""
        with open(_ADO, encoding="utf-8") as fh:
            ado = fh.read()
        body = ado[ado.index("program define _dash_serve_spec"):]
        body = body[:body.index("\nend\n")]
        assert "_dash_is_digits(st_local(\"port\")" in body
        assert "_dash_is_digits(st_local(\"timeout\"), 9)" in body
        assert not re.search(r"regexm\([^)]*`(port|timeout)'", body)

    def test_dash_setup_keeps_only_a_version_made_of_version_characters(self):
        with open(_SETUP, encoding="utf-8") as fh:
            setup = fh.read()
        body = setup[setup.index("program define _dash_pkg_version"):]
        body = body[:body.index("\nend\n")]
        assert 'fullmatch(r"[A-Za-z0-9.+!_-]{1,64}"' in body
        assert 'sfi.Macro.setLocal("_pv", _dash_pv if' in body

    def test_the_spec_line_escapes_every_build_option(self):
        """No valid layout() can hold a backslash or a quote any more
        (P20-30 refuses what is not one of its forms), so P20-17 can no
        longer show the escaping through the command; this pins it.  The
        master spec line wrote layout(), link() and filterposition() raw,
        and layout("bs\\") broke the JSON (r(7102))."""
        with open(_ADO, encoding="utf-8") as fh:
            ado = fh.read()
        line = next(l for l in ado.splitlines()
                    if l.lstrip().startswith("local master_json")
                    and '"kpis"' in l)
        for key, local in (("layout", "_layout_esc"), ("link", "_link_esc"),
                           ("filter_position", "_fpos_esc"),
                           ("theme", "_theme_esc"), ("title", "_title_esc"),
                           ("subtitle", "_subtitle_esc"),
                           ("tabs", "_tabs_esc")):
            assert f'"{key}":"`{local}\'"' in line, key
        body = ado[ado.index("program define _dash_prepare_spec"):]
        body = body[:body.index("\nend\n")]
        for raw, local in (("layout", "_layout_esc"), ("link", "_link_esc"),
                           ("filterposition", "_fpos_esc")):
            assert (f"_dash_json_str `\"`{raw}\'\"\'" in body
                    and local in body), raw

