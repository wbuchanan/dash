"""scripts/svg_text_runs.py: the styled runs of a Stata SVG's texts
(WP-30 P1.11b's truth reader).  Each SVG is written inline in Stata's
dialect (StataNow 19.5, measured 08oct2026)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "scripts"))
import svg_text_runs as sr  # noqa: E402

_H = "font-family:'Helvetica';font-size:112.56px"


def _svg(tmp_path, body):
    p = tmp_path / "g.svg"
    p.write_text('<svg xmlns="http://www.w3.org/2000/svg">' + body + "</svg>",
                 encoding="utf-8")
    return str(p)


class TestTheRunReader:
    def test_plain_text_is_one_run(self, tmp_path):
        got = sr.svg_text_runs(_svg(tmp_path, (
            f'<text x="1" y="2" style="{_H};fill:#000000">3_ab</text>')))
        assert got == [{"x": 1.0, "y": 2.0, "runs": [{
            "text": "3_ab", "weight": "normal", "style": "normal",
            "family": "Helvetica", "size": 112.56, "level": ""}]}]

    def test_tspans_carry_weight_style_family_and_level(self, tmp_path):
        body = (
            '<text x="1" y="2" style="fill:#000000">\n\t\t'
            f'<tspan style="{_H}">R</tspan>\n\t\t'
            "<tspan style=\"font-family:'Times';font-weight:bold;"
            'font-size:112.56px">b</tspan>\n\t\t'
            "<tspan style=\"font-family:'Helvetica';font-style:italic;"
            'font-size:112.56px">i</tspan>\n\t\t'
            '<tspan dy="-47.11px" style="font-size:65.62px">2</tspan>\n\t\t'
            '<tspan dy="59.96px" style="font-size:65.62px">x</tspan>\n\t'
            "</text>")
        runs = sr.svg_text_runs(_svg(tmp_path, body))[0]["runs"]
        assert [(r["text"], r["weight"], r["style"], r["family"], r["level"])
                for r in runs] == [
            ("R", "normal", "normal", "Helvetica", ""),
            ("b", "bold", "normal", "Times", ""),
            ("i", "normal", "italic", "Helvetica", ""),
            ("2", "normal", "normal", "", "sup"),
            ("x", "normal", "normal", "", "sub")]

    def test_nbsp_and_entities_are_read_as_text(self, tmp_path):
        got = sr.svg_text_runs(_svg(tmp_path, (
            f'<text style="{_H}">a  b&amp;&lt;&gt;&quot;</text>')))
        assert got[0]["runs"][0]["text"] == 'a  b&<>"'

    def test_control_codes_are_kept(self, tmp_path):
        got = sr.svg_text_runs(_svg(tmp_path, (
            f'<text style="{_H}">\x01\x81|&#1;&#x1b;&#129;&#150;|'
            "&amp;#1;</text>")))
        assert got[0]["runs"][0]["text"] == (
            "\x01\x81|\x01\x1b\x81\x96|&#1;")

    def test_a_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            sr.svg_text_runs(str(tmp_path / "none.svg"))
