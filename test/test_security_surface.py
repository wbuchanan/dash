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
