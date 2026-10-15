"""WP-31 A4: mla(), ml() and mlal() bind as twoway binds them.

GAPS3 A4 said twoway's mla() is mlalign() (marker_options.sthlp writes
{cmdab:mla:lign}).  Measured 13oct2026 against twoway itself
(test/fixtures/bare_prefix_truth.json mla.*, each spelling's saved .gph
compared with the full option's): ml(make), mla(make), mlab(make) and
mlabe(make) are mlabel(make); mla(center) is "variable center not found",
r(111), as in dash; mlal(), mlali() and mlalign() are mlalign().  So dash's
mlabel() declaration, minimum ml, is twoway's, and what dash lacked was
mlalign() itself: undeclared, mlal(inside) was named in the note as
"mlal()".  MLALign(string) is declared directly after MLabel(), so -syntax-
binds mla() to mlabel() first and mlal() to mlalign(), and mlalign() is
pending -- named in the note -- until WP-31 S34 draws it.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import test_abbreviations as ab  # noqa: E402

ADO = os.path.join(ROOT, "dash.ado")
FIXTURE = os.path.join(HERE, "fixtures", "bare_prefix_truth.json")
REPORT = os.path.join(HERE, "test_unsupported_report_is_true.py")


def _plot_decls():
    src = ab._read(ADO)
    seen, out = set(), []
    for prog in ("_dash_parse_plot_opts", "_dash_parse_graph_opts"):
        for mn, full in ab._syntax_options(ab._program_body(src, prog)):
            if full not in seen:
                seen.add(full)
                out.append((mn, full))
    return out


class TestMlalign:

    def test_declared_keyed_pending(self):
        src = ab._read(ADO)
        body = ab._program_body(src, "_dash_parse_plot_opts")
        assert re.search(r"^\s*MLabel\(string asis\)\s+MLALign\(string\)\s",
                         body, re.M), "MLALign is not declared after MLabel"
        # Flipped (WP-31 E3): mlalign() was pending (named whatever its
        # value), which was wrong once the renderer reads it; it names only
        # outside and an unknown word (test_msangle_mlabstyle.py).
        assert ("if `: length local mlalign' local _dash_pending "
                "`\"`_dash_pending' mlalign\"'") not in body
        assert re.search(r"sreturn local mlalign\s+: copy local mlalign",
                         body)
        keys = re.search(r"foreach key in (mcolor .*?)\{", src, re.S).group(1)
        assert "mlalign" in keys.replace("///", " ").split()

    def test_the_spellings_bind_as_twoways(self):
        with open(FIXTURE, encoding="utf-8") as fh:
            mla = json.load(fh)["mla"]
        decls = _plot_decls()
        bad = []
        for key, r in sorted(mla.items()):
            if r["rc"] != 0:
                continue
            spelling = key.split("_")[0]
            got = ab._resolves_to(spelling, decls)
            if got != r["resolves_to"]:
                bad.append("%s(): twoway %s, dash %s"
                           % (spelling, r["resolves_to"], got))
        assert len([k for k, r in mla.items() if r["rc"] == 0]) == 8
        assert mla["mla_center"]["rc"] == 111
        assert not bad, bad

    def test_counted_and_classified(self):
        with open(REPORT, encoding="utf-8") as fh:
            src = fh.read()
        # Flipped (WP-31 E3): classified in NOT_IN_FILE, not PLOT_VALUES.
        assert re.search(r'"mlalign": "the marker outline', src)
        assert "A4 mlalign declared" in src
