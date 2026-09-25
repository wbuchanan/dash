"""test_svg_truth.py -- WP-28 S02: pins scripts/svg_truth.py, the one reader
for a Stata-exported twoway SVG that every later WP-28 section (13, 14, 15,
16, 18) builds its truth on.

Two fixtures back this module:

* test/fixtures/svg_truth_tiny.svg -- a hand-written SVG in Stata's dialect
  (NOT a Stata export), so every branch of the reader has a pin that Stata
  did not write.  The numbers below are computed by hand from the file's
  coordinates; nothing here is copied from the reader's own output.

  Y AXIS (four ticks, log10): tick pixels 50, 100, 150, 200 (top to bottom)
  carry labels "1000", "100", "10", "1" -- log10(value) is exactly linear in
  pixel (slope -0.02 decade/px).  The plot region is left=50, top=20,
  right=250, bottom=220, so for the y axis edge_start=bottom=220,
  edge_end=top=20:
      inv(220) = 3.0 + (-0.02)*(220-50) = -0.4   -> 10**-0.4 = 0.3981071705534972
      inv(20)  = 3.0 + (-0.02)*(20-50)  =  3.6   -> 10**3.6  = 3981.0717055349722
  low = 0.3981071705534972, high = 3981.0717055349722, space = "log10".

  X AXIS (three ticks): tick pixels 80, 140, 200 carry labels "2019",
  "2020", "Q3" ("Q3" does not parse as a number).  Without tick_values the
  fit uses only the two numeric pairs (80, 2019), (140, 2020), a slope of
  1/60 per px; edge_start=left=50, edge_end=right=250:
      inv(50)  = 2019 + (1/60)*(50-80)  = 2018.5
      inv(250) = 2019 + (1/60)*(250-80) = 2021.8333333333333
  With tick_values=[1, 2, 3] (one entry per tick pixel, ascending: px 80,
  140, 200) the fit is exact through three equally-spaced points, slope
  1/60 per px again but through (80, 1)-(200, 3):
      inv(50)  = 1 + (1/60)*(50-80)  = 0.5
      inv(250) = 1 + (1/60)*(250-80) = 3.8333333333333335

* test/fixtures/svg_truth_smoke.json / .svg -- a real Stata drawing
  (scripts/extract_svg_truth_smoke.do), proving the reader against Stata's
  actual writer and recording the .Graph probe's verdict (D12 provenance
  stamp in _meta).  Missing is a failure (pytest.fail), never a skip: this
  is Stata-measured ground truth the whole package's B1/B2/B3/B5/B6/B7/D1/
  G16/X2 work is built on.

The first collection of this module, before scripts/svg_truth.py existed,
failed with ModuleNotFoundError: that is the section's regression (recorded
at task 02-01, before scripts/svg_truth.py was written).
"""
import math
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))
sys.path.insert(0, _HERE)

import svg_truth  # noqa: E402  (path insert must precede this import)

_FIXTURES = os.path.join(_HERE, "fixtures")
TINY = os.path.join(_FIXTURES, "svg_truth_tiny.svg")
SMOKE_JSON = os.path.join(_FIXTURES, "svg_truth_smoke.json")
SMOKE_SVG = os.path.join(_FIXTURES, "svg_truth_smoke.svg")
CERT_SVG_DO = os.path.join(_HERE, "cert_svg.do")
SMOKE_DO = os.path.join(_ROOT, "scripts", "extract_svg_truth_smoke.do")
GAPS2_CSCRIPT = os.path.join(_HERE, "test_gaps2_truth.cscript")


@pytest.fixture(scope="module")
def smoke():
    # Stata-measured ground truth: missing is a defect (PRD Sec.8 "no
    # skips"), not a reason to skip every check below that reads it.
    if not os.path.exists(SMOKE_JSON):
        pytest.fail(f"section 02 fixture missing: {SMOKE_JSON}")
    if not os.path.exists(SMOKE_SVG):
        pytest.fail(f"section 02 fixture missing: {SMOKE_SVG}")
    import json
    with open(SMOKE_JSON, encoding="utf-8") as fh:
        return json.load(fh)


def _one_tick_svg(tmp_path):
    """A minimal SVG with exactly one labelled numeric tick -- fewer than
    the two pairs an extent fit needs."""
    p = tmp_path / "one_tick.svg"
    p.write_text(
        '<svg viewBox="0 0 100 100">'
        '<rect x="0" y="0" width="100" height="100" style="fill:#FFFFFF;"/>'
        '<rect x="20" y="10" width="60" height="60" style="fill:#FFFFFF;"/>'
        '<line x1="15" y1="40" x2="20" y2="40" style="stroke:#000000;"/>'
        '<text x="5" y="40" style="font-size:8px;">5</text>'
        '</svg>',
        encoding="utf-8",
    )
    return str(p)


class TestTexts:

    def test_nbsp_is_read_as_a_space(self):
        texts = svg_truth.svg_texts(TINY)
        entity = next(t for t in texts if t["raw"] == "Two&#160;words")
        literal = next(t for t in texts if t["raw"] == "Two words")
        assert entity["text"] == "Two words"
        assert literal["text"] == "Two words"
        assert " " in literal["raw"]

    def test_position_size_anchor_fill_and_rotation_are_read(self):
        texts = svg_truth.svg_texts(TINY)
        title = next(t for t in texts if t["raw"] == "Two&#160;words")
        assert title["anchor"] == "middle"
        assert title["x"] == 150.0 and title["y"] == 15.0
        assert title["size"] == 11.0
        legend = next(t for t in texts if t["raw"] == "Two words")
        assert legend["anchor"] is None
        ytitle = next(t for t in texts if t["text"] == "Y Title")
        assert ytitle["rotate"] == -90.0
        assert ytitle["fill"] == "#000000"

    def test_svg_has_text_matches_the_whole_element_exactly_and_lower_optionally(self):
        assert svg_truth.svg_has_text(TINY, "Y Title") == 1
        assert svg_truth.svg_has_text(TINY, "y title") == 0
        assert svg_truth.svg_has_text(TINY, "y title", lower=True) == 1
        # A substring of an element's text is not a match: the point of
        # "matches the whole element" is that "Title" alone must not hit.
        assert svg_truth.svg_has_text(TINY, "Title") == 0
        assert svg_truth.svg_has_text(TINY, "Two words") == 2


class TestFills:

    def test_fills_are_grouped_by_colour_with_counts_and_kinds(self):
        fills = svg_truth.svg_fills(TINY)
        assert fills["#1a476f"]["n"] == 3
        assert fills["#1a476f"]["kinds"] == {"circle": 3}
        assert fills["#1a476f"]["opacity"] == []
        assert fills["#90353b"]["n"] == 2
        assert fills["#90353b"]["kinds"] == {"circle": 1, "path": 1}
        assert fills["#90353b"]["opacity"] == [0.2]

    def test_marker_fills_exclude_rects(self):
        markers = svg_truth.svg_marker_fills(TINY)
        assert "#ffffff" not in markers
        assert "#1a476f" in markers and "#90353b" in markers
        all_fills = svg_truth.svg_fills(TINY)
        assert "#ffffff" in all_fills


class TestLines:

    def test_horizontal_vertical_and_diagonal_lines_are_split_and_grouped(self):
        lines = svg_truth.svg_lines(TINY)
        groups = svg_truth.line_groups(lines["h"], "y1")
        dashed = [g for g in groups if g["stroke"] == "#c8c8c8"]
        assert len(dashed) == 1
        assert dashed[0]["n_segments"] == 5
        assert len(lines["diag"]) == 1
        assert lines["diag"][0]["stroke"] == "#888888"
        # The y-axis tick marks are horizontal; the x-axis tick marks are
        # vertical -- both black, distinct from the dashed grey gridline.
        assert sum(1 for d in lines["h"] if d["stroke"] == "#000000") == 4
        assert sum(1 for d in lines["v"] if d["stroke"] == "#000000") == 3


class TestPlotregion:

    def test_the_first_solid_non_canvas_rect_is_the_plotregion(self):
        pr = svg_truth.svg_plotregion(TINY)
        assert pr["left"] == 50.0 and pr["top"] == 20.0
        assert pr["right"] == 250.0 and pr["bottom"] == 220.0
        assert pr["fill"] == "#ffffff"


class TestAxisExtent:

    def test_a_log_axis_is_fitted_in_log_space(self):
        ext = svg_truth.svg_axis_extent(TINY, "y")
        assert ext is not None
        assert ext["space"] == "log10"
        assert ext["reversed"] is False
        assert ext["n_ticks"] == 4
        assert math.isclose(ext["low"], 10 ** -0.4, rel_tol=1e-9)
        assert math.isclose(ext["high"], 10 ** 3.6, rel_tol=1e-9)

    def test_supplied_tick_values_replace_unreadable_labels(self):
        with_values = svg_truth.svg_axis_extent(TINY, "x", tick_values=[1, 2, 3])
        assert with_values["space"] == "linear"
        assert math.isclose(with_values["low"], 0.5, rel_tol=1e-9)
        assert math.isclose(with_values["high"], 23 / 6, rel_tol=1e-9)

        without_values = svg_truth.svg_axis_extent(TINY, "x")
        assert without_values["n_ticks"] == 3
        assert math.isclose(without_values["low"], 2018.5, rel_tol=1e-9)
        assert math.isclose(without_values["high"], 2019 + 170 / 60,
                            rel_tol=1e-9)

    def test_a_length_mismatch_in_tick_values_raises(self):
        with pytest.raises(ValueError) as exc:
            svg_truth.svg_axis_extent(TINY, "x", tick_values=[1, 2])
        assert "2" in str(exc.value) and "3" in str(exc.value)

    def test_fewer_than_two_pairs_returns_none_with_a_reason(self, tmp_path):
        path = _one_tick_svg(tmp_path)
        ext = svg_truth.svg_axis_extent(path, "y")
        assert ext is None
        assert "fewer than two" in svg_truth.svg_axis_extent.last_reason


class TestTheSmokeFixture:

    def test_the_module_reads_the_committed_stata_svg_as_the_fixture_records(self, smoke):
        assert svg_truth.svg_texts(SMOKE_SVG) == smoke["texts"]
        assert svg_truth.svg_marker_fills(SMOKE_SVG) == smoke["marker_fills"]
        y_ext = svg_truth.svg_axis_extent(SMOKE_SVG, "y")
        x_ext = svg_truth.svg_axis_extent(SMOKE_SVG, "x")
        for key in ("low", "high", "residual"):
            assert math.isclose(y_ext[key], smoke["y_extent"][key], abs_tol=1e-9)
            assert math.isclose(x_ext[key], smoke["x_extent"][key], abs_tol=1e-9)
        assert y_ext["space"] == smoke["y_extent"]["space"]
        assert x_ext["space"] == smoke["x_extent"]["space"]

    def test_title_axis_title_and_legend_text_are_found_once_each(self, smoke):
        assert svg_truth.svg_has_text(SMOKE_SVG, "Smoke  title") == 1
        assert svg_truth.svg_has_text(SMOKE_SVG, "Miles per gallon") == 1
        assert svg_truth.svg_has_text(SMOKE_SVG, "Domestic cars") == 1
        assert svg_truth.svg_has_text(SMOKE_SVG, "Foreign cars") == 1
        # One space, not two: the point of the nbsp case.
        assert svg_truth.svg_has_text(SMOKE_SVG, "Smoke title") == 0
        assert smoke["title"]["found"] == 1
        assert smoke["legend"]["found"] == [1, 1]

    def test_two_marker_fills_of_53_and_23_elements(self, smoke):
        # Auto's 52 domestic + 22 foreign cars, plus one legend swatch per
        # series (also a <circle>, also filled in the series colour) --
        # measured 25sep2026: svg_marker_fills makes no distinction between
        # a data point and a legend key's sample marker, both legitimately
        # <circle> elements.  53 = 52 + 1, 23 = 22 + 1.
        fills = svg_truth.svg_marker_fills(SMOKE_SVG)
        counts = sorted(info["n"] for info in fills.values())
        assert counts == [23, 53]
        assert smoke["marker_fills"] == fills

    def test_the_y_extent_covers_range_0_60_and_the_x_extent_covers_the_data(self, smoke):
        y_ext = svg_truth.svg_axis_extent(SMOKE_SVG, "y")
        x_ext = svg_truth.svg_axis_extent(SMOKE_SVG, "x")
        assert y_ext["low"] <= 0
        assert y_ext["high"] >= 60
        assert x_ext["low"] <= 1760
        assert x_ext["high"] >= 4840

    def test_the_graph_probe_is_recorded_with_a_verdict(self, smoke):
        drawn = smoke["graph_probe"]["drawn"]["y"]
        for key in ("min", "max", "curmin", "curmax",
                    "major_min", "major_max", "major_delta"):
            assert key in drawn
        assert isinstance(smoke["matches_svg"]["drawn_extent_member"], str)
        member = smoke["matches_svg"]["drawn_extent_member"]
        if member != "none":
            assert smoke["matches_svg"].get(member) is True

    def test_the_cert_programs_agreed_with_the_module(self, smoke):
        for rec in smoke["cert_programs"]:
            if rec["program"] == "cert_svg_texts":
                assert rec["n"] == len(smoke["texts"])
            elif rec["program"] == "cert_svg_has_text":
                pass  # spot-checked by test_title_axis_title...
            elif rec["program"] == "cert_svg_fills":
                if "colours" in rec:
                    assert set(rec["colours"]) <= set(smoke["marker_fills"])
            elif rec["program"] == "cert_svg_extent":
                assert rec["axis"] in ("x", "y")

    def test_the_fixture_names_its_stata_and_scheme(self, smoke):
        meta = smoke["_meta"]
        assert meta["stata_version"]
        assert meta["scheme"]
        assert "yscale(range(0 60))" in meta["command"]

    def test_the_meta_stamp_holds_the_four_provenance_keys(self, smoke):
        meta = smoke["_meta"]
        for key in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert key in meta
            assert isinstance(meta[key], str) and meta[key]
        assert re.fullmatch(r"[0-9a-f]{40}", meta["dash_commit"])


class TestScriptHygiene:

    def test_the_smoke_script_python_block_has_no_backtick_and_no_stata_call(self):
        if not os.path.exists(SMOKE_DO):
            pytest.fail(f"section 02 fixture missing: {SMOKE_DO}")
        with open(SMOKE_DO, encoding="utf-8") as fh:
            lines = fh.readlines()
        # A standalone "python:" LINE, not the header comment's prose about
        # python: blocks (the header discusses the trap by name).
        start = next(i for i, l in enumerate(lines) if l.strip() == "python:")
        block = "".join(lines[start:])
        assert "`" not in block
        assert "SFIToolkit.stata" not in block
        assert re.search(r"(?<!\w)stata\s*\(", block) is None

    def test_cert_svg_do_interpolates_no_macro_into_python(self):
        if not os.path.exists(CERT_SVG_DO):
            pytest.fail(f"section 02 fixture missing: {CERT_SVG_DO}")
        with open(CERT_SVG_DO, encoding="utf-8") as fh:
            lines = fh.readlines()
        # The one top-level `python: ... end' block (the six Stata programs
        # that follow it close with `end' too, so the search must stop at
        # the FIRST standalone `end' after the FIRST standalone `python:',
        # not the last `end' in the file).
        start = next(i for i, l in enumerate(lines) if l.strip() == "python:")
        stop = next(i for i in range(start + 1, len(lines))
                    if lines[i].strip() == "end")
        block = "".join(lines[start:stop])
        assert "`" not in block
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("python:") and stripped != "python:":
                # Each one-liner qualifies through __main__ (see the file's
                # header trap note): a bare `_cert_svg_xxx()' call raises
                # NameError when the statement lives inside a `program
                # define' body, even though the function is defined at the
                # do-file's top level.
                assert re.fullmatch(
                    r"python:\s*import __main__ as (\w+);\s*"
                    r"\1\._cert_svg_\w+\(\)", stripped), stripped

    def test_the_module_imports_nothing_but_the_stdlib(self):
        import ast
        with open(os.path.join(_ROOT, "scripts", "svg_truth.py"),
                  encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        assert names, "the module imports nothing at all"
        assert names <= set(sys.stdlib_module_names), names

    def test_the_truth_script_has_the_block_scaffolding(self):
        if not os.path.exists(GAPS2_CSCRIPT):
            pytest.fail(f"section 02 fixture missing: {GAPS2_CSCRIPT}")
        with open(GAPS2_CSCRIPT, encoding="utf-8") as fh:
            text = fh.read()
        order = [
            "SKIP: Python not available.",
            'do "cert_helpers.do"',
            'do "cert_svg.do"',
            "* ==== S02 helper smoke: the cert_svg programs ====",
            "local only : env GAPS2_ONLY",
            "* ==== end S02 ====",
            "* ==== append new blocks above this line ====",
        ]
        positions = [text.index(s) for s in order]
        assert positions == sorted(positions), (order, positions)
        assert "capture python:" not in text
