"""WP-30 P1.27: dash reads twoway's command form.

A leading twoway, tw, two or graph twoway is read off once; one saving()
grammar, twoway's, serves the one-line form and dash build, read from the
text as typed; the To launch: line is quoted for the shell; no window
opens in batch or after set graphics off.  These tests read dash.ado and
dash.sthlp as text; the behaviour is certified by
test_path_validation.cscript PV-35..44, test_serve_browser.cscript
SB-31..38 and test_wp30_truth.cscript CF-01..07.
"""
import glob
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _program_body(name):
    """Program *name*'s lines in dash.ado, ``//`` comments dropped."""
    lines = _read("dash.ado").splitlines()
    start = next(i for i, l in enumerate(lines)
                 if re.match(rf"program define {re.escape(name)}\b", l))
    end = next(i for i in range(start + 1, len(lines))
               if lines[i].strip() == "end")
    return "\n".join(l.split("//", 1)[0] for l in lines[start:end])


class TestOneSavingGrammar:

    def test_every_route_calls_the_one_parser(self):
        for name in ("_dash_render_immediate", "_dash_build", "_dash_plot"):
            assert "_dash_saving_parse(" in _program_body(name), name

    def test_no_route_reads_replace_with_a_regex(self):
        # name()'s own ", replace" (twoway's name(n, replace)) is not saving().
        code = "\n".join([_program_body("_dash_render_immediate"),
                          _program_body("_dash_build")]
                         + [l for l in _program_body("_dash_plot").splitlines()
                            if "g_saving" in l])
        assert not re.search(r"replace\[ \\t\]\*\$", code)

    def test_saving_is_read_as_typed(self):
        assert "SAVing(string asis)" in _program_body("_dash_build")
        assert "_dash_seg_saving(" in _program_body("_dash_plot")


class TestTheLaunchLine:

    def test_the_server_banner_quotes_the_path_for_the_shell(self):
        body = _program_body("_dash_build")
        assert "_dash_launch_quote(" in body
        assert "_dash_launch_warn(" in body
        assert '"  To launch: python " + char(34)' not in _read("dash.ado")


class TestTheDisplayRule:

    def test_the_seam_is_read_only_by_the_deciders_and_never_documented(self):
        lines = _read("dash.ado").splitlines()
        owner = None
        hits = set()
        for l in lines:
            m = re.match(r"program define (\S+?)(,|\s|$)", l)
            if m:
                owner = m.group(1)
            if "dash__display" in l.split("//", 1)[0]:
                hits.add(owner)
        assert hits == {"_dash_browser_wanted", "_dash_dashboard_browser"}
        shipped = (glob.glob(os.path.join(_ROOT, "*.sthlp"))
                   + glob.glob(os.path.join(_ROOT, "*.pkg"))
                   + [os.path.join(_ROOT, f) for f in
                      ("CHANGELOG.md", "README.md")
                      if os.path.exists(os.path.join(_ROOT, f))])
        for path in shipped:
            with open(path, encoding="utf-8") as fh:
                assert "dash__display" not in fh.read(), path

    def test_the_prefix_strip_follows_the_guards(self):
        body = _program_body("dash")
        a = body.index("_dash_require_mata")
        b = body.index("_dash_strip_prefix()")
        c = body.index('"`_subcmd\'" ==')
        assert a < b < c


class TestTheHelpStatesTheCommandForm:

    def _help(self):
        return _read("dash.sthlp")

    def test_the_syntax_names_the_prefixes(self):
        h = self._help()
        assert "{cmd:graph twoway}" in h
        assert "twoway is not a twoway plot type" in h
        assert "command twow is unrecognized" in h

    def test_saving_takes_replace_and_asis_on_every_route(self):
        h = self._help()
        assert "{cmd:replace} {cmd:asis}]{cmd:)}" in h
        assert "option bogus not allowed" in h

    def test_the_browser_rule_names_batch_and_graphics_off(self):
        h = self._help()
        assert "{ul:Batch and set graphics off.}" in h
        assert "{cmd:set graphics off}" in h

    def test_the_character_rule_is_the_final_one(self):
        h = self._help()
        assert "{cmd:..} traversal allowed" not in h
        assert "traversal allowed" not in h
        assert "must end in {cmd:.py}" not in h
        assert "{marker saving_chars}" in h
        for kind in ("a double quote", "a backquote", "a dollar sign",
                     "a control character", "starting with {cmd:-}"):
            assert kind in h, kind
