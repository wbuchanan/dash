"""scatteri and pci: the renderer's half of their immediate values.

Measured 23sep2026 with the console binary at ad13a0f: dash.ado wrote the
tokens of ``scatteri`` and ``pci`` into the spec as they were typed, so
``dash pci 0 0 0 abc``, ``dash pci 0 0 0 1 (3) "A" 0 0 1 0`` and
``dash scatteri .5 3000`` registered with rc 0 and the render stopped on a
JSONDecodeError, r(7102).  dash.ado now reads both with the reader
pcarrowi's values go through (dash_parse.mata section 2c,
test_parser.cscript P1A-60..67) and writes one record per point or segment:

* scatteri: ``[y, x]``, or ``[y, x, "label", clock]`` with clock null when
  only a label is given -- ``scatteri 1 2 (9) "A" 3 4`` is
  ``[[1,2,"A",9],[3,4]]``;
* pci: ``[y1, x1, y2, x2]`` or ``[y1, x1, y2, x2, "label", clock]``, the
  record pcarrowi writes -- it was ``[[y1,x1],[y2,x2]]``, two points the
  renderer paired up again;
* a missing coordinate is null.

What twoway draws, measured from the serset each command draws and from
its SVG export: a missing coordinate draws nothing, and its label nothing;
a scatteri label sits at its point, placed by its own clock position, else
by mlabposition(), else at 3 o'clock; a clock position that is not a whole
number -- 3.5, which twoway accepts -- is drawn at 12 o'clock, twoway noting
"named style 3.5 not found in class clockdir, default attributes used";
and twoway pci, an immediate pcspike, draws no label whatever it is given.

Both render modes draw through the same GlyphMapper methods; the last class
holds them to it, the served app built and run as ``dash serve`` runs it.
"""
import itertools
import math
import os
import sys
import time
import warnings

import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource, LabelSet, Plot
from bokeh.models.glyphs import Scatter, Segment
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_spec  # noqa: E402
from test_adversarial_matrix import (_app_source, _load_app,  # noqa: E402
                                     _session, _write_inputs)

NAN = float("nan")
# WP-30 P1.12a (Evidence E5, twoway measured): under s2color a label sits
# (marker radius + gap) from its point: symbolsize medium 1.52778 rs
# (1 rs = 2.88 pt = 3.84 px) halved, plus gsize label_gap 2 pt.
_D = round(1.52778 * 2.88 * (4 / 3) / 2 + 2 * (4 / 3), 4)   # 5.6 px
_SEQ = itertools.count()


from conftest import render_models  # noqa: E402


def _labelsets(fig):
    return [r for r in fig.center if isinstance(r, LabelSet)]


def _text_field(ls):
    return ls.text if isinstance(ls.text, str) else ls.text.field


def _labels_of(fig):
    """(x_offset, y_offset, texts, xs, ys) per LabelSet, sorted."""
    out = []
    for ls in _labelsets(fig):
        data = ls.source.data
        xf = ls.x if isinstance(ls.x, str) else ls.x.field
        yf = ls.y if isinstance(ls.y, str) else ls.y.field
        # Offsets rounded to 4 places: WP-30 P1.12a's offsets are products
        # of Stata's scheme numbers (5.6000043 px), compared as literals.
        out.append((round(ls.x_offset, 4), round(ls.y_offset, 4),
                    tuple(str(v) for v in data[_text_field(ls)]),
                    tuple(float(v) for v in data[xf]),
                    tuple(float(v) for v in data[yf])))
    return sorted(out)


def _col(renderer, attr):
    field = getattr(renderer.glyph, attr)
    field = field if isinstance(field, str) else getattr(field, "field", field)
    return [float(v) for v in renderer.data_source.data[field]]


def _draw(method, values, options=None, color_idx=0):
    """(mapper, figure, returned renderers, warning texts) for one layer."""
    fig = figure()
    gm = dr.GlyphMapper()
    # Notes are once per render (_DASH_NOTED); each draw here is one.
    dr._dash_reset_notes()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        out = getattr(gm, method)(fig, values, dict(options or {}),
                                  color_idx=color_idx)
    return gm, fig, out, [str(w.message) for w in caught]


# ===========================================================================
# scatteri
# ===========================================================================

class TestScatteriDrawsItsRecords:
    def test_a_missing_coordinate_draws_no_point_and_no_label(self):
        """``scatteri . 3000 "A" 30 4000 "B"``: twoway draws the second."""
        _, fig, (r,), _ = _draw("map_scatteri",
                                [[None, 3000, "A", None], [30, 4000, "B", 3],
                                 [5, None], [None, None, "C", 12]])
        assert isinstance(r.glyph, Scatter)
        assert _col(r, "x") == [4000.0]
        assert _col(r, "y") == [30.0]
        # WP-30 P1.12a (Evidence E5, twoway measured): a label sits radius
        # + default gap, 2.93334 + 2.66667 = 5.6 px, along its clock.
        assert _labels_of(fig) == [(_D, 0, ("B",), (4000.0,), (30.0,))]

    def test_a_non_finite_coordinate_is_missing(self):
        _, _, (r,), _ = _draw("map_scatteri",
                              [[float("inf"), 1], [2, float("-inf")], [3, 4]])
        assert _col(r, "x") == [4.0] and _col(r, "y") == [3.0]

    def test_a_label_sits_at_its_point_at_its_clock_position(self):
        _, fig, _, _ = _draw("map_scatteri",
                             [[1, 2, "nine", 9], [3, 4, "six", 6],
                              [5, 6, "zero", 0], [7, 8, "twelve", 12]])
        # WP-30 P1.12a (Evidence E5, twoway measured): a label sits radius
        # + default gap, 2.93334 + 2.66667 = 5.6 px, along its clock.
        assert _labels_of(fig) == [
            (-_D, 0, ("nine",), (2.0,), (1.0,)),
            (0, -_D, ("six",), (4.0,), (3.0,)),
            (0, 0, ("zero",), (6.0,), (5.0,)),
            (0, _D, ("twelve",), (8.0,), (7.0,)),
        ]

    def test_a_label_without_a_clock_takes_mlabposition(self):
        """twoway: mlabposition() places a label given no clock position
        (measured: both labels at 9 o'clock); one with a clock keeps its
        own."""
        _, fig, _, _ = _draw("map_scatteri",
                             [[1, 2, "A", None], [3, 4, "B", 6]],
                             {"mlabposition": "9"})
        # WP-30 P1.12a (Evidence E5, twoway measured): a label sits radius
        # + default gap, 2.93334 + 2.66667 = 5.6 px, along its clock.
        assert _labels_of(fig) == [(-_D, 0, ("A",), (2.0,), (1.0,)),
                                   (0, -_D, ("B",), (4.0,), (3.0,))]

    def test_a_label_without_a_clock_or_mlabposition_is_at_three(self):
        _, fig, _, _ = _draw("map_scatteri", [[1, 2, "A", None], [3, 4, "B"]])
        # WP-30 P1.12a (Evidence E5, twoway measured): a label sits radius
        # + default gap, 2.93334 + 2.66667 = 5.6 px, along its clock.
        assert _labels_of(fig) == [(_D, 0, ("A", "B"), (2.0, 4.0),
                                    (1.0, 3.0))]

    def test_a_clock_that_is_not_a_whole_number_is_drawn_at_twelve(self):
        """twoway accepts (3.5) and draws its label above the point, at 12
        o'clock, with a note: "named style 3.5 not found in class clockdir,
        default attributes used" (measured from its SVG export)."""
        _, fig, _, warns = _draw("map_scatteri",
                                 [[1, 2, "A", 3.5], [3, 4, "B", 7.25],
                                  [5, 6, "C", 3]])
        # WP-30 P1.12a (Evidence E5, twoway measured): a label sits radius
        # + default gap, 2.93334 + 2.66667 = 5.6 px, along its clock.
        assert _labels_of(fig) == [(0, _D, ("A", "B"), (2.0, 4.0),
                                    (1.0, 3.0)),
                                   (_D, 0, ("C",), (6.0,), (5.0,))]
        notes = [w for w in warns if "scatteri" in w and "clock" in w]
        assert len(notes) == 1, warns
        assert "3.5" in notes[0] and "7.25" in notes[0]
        assert "12" in notes[0]

    def test_an_empty_label_or_a_lone_clock_draws_no_label(self):
        """Only the labelled point is labelled: an empty label is none, and
        a clock position places a label, it is not one (twoway, measured:
        ``scatteri 1 2 (6) "A" 3 4 (9)`` draws the one label)."""
        _, fig, (r,), _ = _draw("map_scatteri",
                                [[1, 2, "", 9], [3, 4, "", None],
                                 [5, 6, "E", 6]])
        # WP-30 P1.12a (Evidence E5, twoway measured): a label sits radius
        # + default gap, 2.93334 + 2.66667 = 5.6 px, along its clock.
        assert _labels_of(fig) == [(0, -_D, ("E",), (6.0,), (5.0,))]
        assert _col(r, "x") == [2.0, 4.0, 6.0]

    def test_the_label_style_options_apply(self):
        gm, fig, _, _ = _draw("map_scatteri", [[1, 2, "A", 3]],
                              {"mlabcolor": "red", "mlabsize": "large"})
        (ls,) = _labelsets(fig)
        assert ls.text_color == gm.tr.translate_mcolor("red")
        # WP-30 P1.12a (Evidence E5, twoway measured): label sizes are CSS
        # points; gsize large is 4.8611 units x 2.88 = 14pt.
        assert ls.text_font_size == "14pt"

    def test_an_immediate_label_replaces_mlabel(self):
        """twoway: ``scatteri 1 2 "A", mlabel(make)`` draws "A" (measured);
        ``scatteri 1 2, mlabel(make)`` draws no label at all."""
        _, fig, _, _ = _draw("map_scatteri", [[1, 2, "A", None]],
                             {"mlabel": "make"})
        # WP-30 P1.12a (Evidence E5, twoway measured): a label sits radius
        # + default gap, 2.93334 + 2.66667 = 5.6 px, along its clock.
        assert _labels_of(fig) == [(_D, 0, ("A",), (2.0,), (1.0,))]
        _, fig, _, _ = _draw("map_scatteri", [[1, 2]], {"mlabel": "make"})
        assert not _labelsets(fig)

    def test_a_record_without_a_clock_field_still_labels(self):
        """``[y, x, "label"]``, the shape dash.ado wrote before the clock."""
        _, fig, _, _ = _draw("map_scatteri", [[20, 3000, "A"], [30, 4000, "B"]])
        # WP-30 P1.12a (Evidence E5, twoway measured): a label sits radius
        # + default gap, 2.93334 + 2.66667 = 5.6 px, along its clock.
        assert _labels_of(fig) == [(_D, 0, ("A", "B"), (3000.0, 4000.0),
                                    (20.0, 30.0))]

    def test_the_label_is_text_not_markup(self):
        payload = '<img src=x onerror=alert(1)>{bf:X}"],"expr":"1'
        _, fig, _, _ = _draw("map_scatteri", [[0, 1, payload, 12]])
        (ls,) = _labelsets(fig)
        # Flipped (WP-30 P1.11b): {bf:X} is graph-text markup, which twoway
        # draws as the bold text; the label stays text, never HTML or
        # script, and the raw column still holds the payload.
        assert list(ls.source.data[_text_field(ls)]) == [
            payload.replace("{bf:X}", "X")]
        assert payload in [v for c in ls.source.data.values() for v in c]
        # WP-30 P1.12a (Evidence E5, twoway measured): 12 o'clock is
        # radius + default gap, 2.93334 + 2.66667 px, straight up.
        assert ls.x_offset == 0
        assert ls.y_offset == pytest.approx(_D, abs=1e-4)

    @pytest.mark.parametrize("bad", [
        [[1, 2, "a", 3, 9]], [[True, 1]], [[1, False]], [{"y": 1, "x": 2}],
    ])
    def test_a_malformed_record_is_named(self, bad):
        """A spec written by hand is an input too: a record that is not two
        numbers, a label and a clock position is refused naming the type.
        A bool is not a number, though float() takes it."""
        with pytest.raises(ValueError, match="scatteri"):
            dr.GlyphMapper().map_scatteri(figure(), bad, {})

    def test_a_hundred_thousand_records_are_read_in_bounded_time(self):
        values = [[i, i + 1, "", None] for i in range(100_000)]
        t0 = time.perf_counter()
        coords, labels, clocks = dr.GlyphMapper._immediate_records(
            values, "scatteri", 2)
        assert time.perf_counter() - t0 < 5.0
        assert len(coords) == 2 and len(coords[0]) == 100_000
        assert len(labels) == len(clocks) == 100_000


# ===========================================================================
# pci
# ===========================================================================

class TestPciDrawsItsRecords:
    def test_one_segment_per_record(self):
        _, _, (r,), _ = _draw("map_pci_literal",
                              [[20, 3000, 30, 4000], [0, 0, 1, 0]])
        assert isinstance(r.glyph, Segment)
        assert _col(r, "x0") == [3000.0, 0.0]
        assert _col(r, "y0") == [20.0, 0.0]
        assert _col(r, "x1") == [4000.0, 0.0]
        assert _col(r, "y1") == [30.0, 1.0]

    def test_labels_and_clock_positions_are_not_drawn(self):
        """twoway pci is an immediate pcspike: its serset carries the label
        and no label reaches its SVG, with mlabcolor() or without."""
        _, fig, (r,), _ = _draw("map_pci_literal",
                                [[0, 0, 0, 1, "A", 3], [0, 0, 1, 0, "B", None],
                                 [1, 1, 2, 2, "C", 3.5]],
                                {"mlabcolor": "red", "mlabposition": "9"})
        assert not _labelsets(fig)
        assert len(_col(r, "x0")) == 3

    def test_a_missing_coordinate_draws_no_segment(self):
        _, _, (r,), _ = _draw("map_pci_literal",
                              [[None, 0, 0, 1], [1, 1, 2, 2],
                               [0, float("inf"), 1, 1]])
        assert _col(r, "x0") == [1.0] and _col(r, "y1") == [2.0]

    def test_the_old_two_point_shape_is_named_not_redrawn(self):
        """``[[20,3000],[30,4000]]`` is what dash.ado wrote before; a spec
        is an input too, and a record that is not one is named."""
        with pytest.raises(ValueError, match="pci"):
            dr.GlyphMapper().map_pci_literal(
                figure(), [[20.0, 3000.0], [30.0, 4000.0]], {})

    @pytest.mark.parametrize("bad", [
        [[0, 0, "x", 1]], [[0, 0, 1]], [[0, 0, 1, 1, "a", 3, 9]],
        [[0, 0, True, 1]],
    ])
    def test_a_malformed_record_is_named(self, bad):
        with pytest.raises(ValueError, match="pci"):
            dr.GlyphMapper().map_pci_literal(figure(), bad, {})

    def test_the_line_options_style_the_segment(self):
        gm, _, (r,), _ = _draw("map_pci_literal", [[0, 0, 1, 1]],
                               {"lcolor": "magenta", "lwidth": "thick"})
        assert _col(r, "x0") == [0.0] and _col(r, "y1") == [1.0]
        # Magenta, in no s2color slot: this set navy, the segment's own
        # default, and passed with lcolor() taken away (measured 24sep2026).
        assert r.glyph.line_color == "#ff00ff"
        assert r.glyph.line_width == gm.tr.translate_lwidth("thick")

    def test_a_hundred_thousand_records_are_read_in_bounded_time(self):
        values = [[i, i, i + 1, i + 1] for i in range(100_000)]
        t0 = time.perf_counter()
        _, fig, (r,), _ = _draw("map_pci_literal", values)
        assert time.perf_counter() - t0 < 10.0
        assert len(_col(r, "x0")) == 100_000


# ===========================================================================
# The record reader both share with pcarrowi
# ===========================================================================

class TestTheRecordReader:
    def test_it_reads_coordinates_labels_and_clocks(self):
        coords, labels, clocks = dr.GlyphMapper._immediate_records(
            [[1, 2, "A", 9], [3, 4], [None, 5, "", 3.5], [6, 7, "B", None],
             [8, 9, "C", 12.0]], "scatteri", 2)
        ys, xs = coords
        assert ys[:2] == [1.0, 3.0] and math.isnan(ys[2])
        assert xs == [2.0, 4.0, 5.0, 7.0, 9.0]
        assert labels == ["A", "", "", "B", "C"]
        assert clocks == ["9", None, "3.5", None, "12"]

    def test_pcarrowis_reader_is_the_same_reader(self):
        values = [[0, 0, 0, 1, "A", 3], [1, None, 2, 2]]
        y1, x1, y2, x2, labels, clocks = dr.GlyphMapper._pc_immediate_records(
            values, "pcarrowi")
        coords, labels2, clocks2 = dr.GlyphMapper._immediate_records(
            values, "pcarrowi", 4)
        assert [y1, x1, y2, x2][0] == coords[0]
        assert math.isnan(x1[1]) and math.isnan(coords[1][1])
        assert (labels, clocks) == (labels2, clocks2)


# ===========================================================================
# pcarrowi: a clock position that is not a whole number
# ===========================================================================

class TestPcarrowiDrawsAnOddClockWhereTwowayDoes:
    def test_it_is_drawn_at_twelve(self):
        """twoway pcarrowi 0 0 0 1 (3.5) "A": the label above the tail,
        where (12) puts it (measured from the SVG export)."""
        _, fig, _, warns = _draw("map_pcarrowi",
                                 [[0, 0, 0, 1, "A", 3.5],
                                  [1, 1, 2, 2, "B", 12]])
        # WP-30 P1.12a (Evidence E5, twoway measured): pcarrow's origin is
        # half the scheme marker size, 2.93334 + gap 2.66667 = 5.6 px.
        assert [(dx, dy, t) for (dx, dy, t, _, _) in _labels_of(fig)] == \
            [(0, _D, ("A", "B"))]
        notes = [w for w in warns if "pcarrowi" in w and "clock" in w]
        assert len(notes) == 1 and "3.5" in notes[0], warns


# ===========================================================================
# Both modes
# ===========================================================================

def _standalone(tmp_path, spec):
    sp, dp = _write_inputs(tmp_path, spec)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return list(r.figures.values()), [str(w.message) for w in caught]


def _served(tmp_path, spec):
    ns = _load_app(_app_source(tmp_path, spec), "imm_%d" % next(_SEQ))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        ns["make_document"](doc)
    return list(doc.select({"type": Plot})), [str(w.message) for w in caught]


def _glyphs(figs):
    out = []
    for f in figs:
        for r in f.renderers:
            g = getattr(r, "glyph", None)
            if g is None:
                continue
            data = r.data_source.data
            coords = {a: [float(v) for v in data[getattr(g, a)]]
                      for a in ("x0", "y0", "x1", "y1", "x", "y")
                      if isinstance(getattr(g, a, None), str)
                      and getattr(g, a) in data}
            out.append((type(g).__name__, coords))
    return out


def _all_labels(figs):
    return sorted(lab for f in figs for lab in _labels_of(f))


def _notes(warns, ptype):
    return sorted(w for w in warns if ptype in w)


class TestBothModesDrawTheSame:
    def _pair(self, tmp_path, plot):
        spec = make_spec([plot])
        s_figs, s_w = _standalone(tmp_path, spec)
        v_figs, v_w = _served(tmp_path, spec)
        return s_figs, v_figs, s_w, v_w

    def test_scatteri_with_labels_clocks_and_a_missing_point(self, tmp_path):
        plot = {"type": "scatteri", "options": {"mlabcolor": "navy"},
                "values": [[20.0, 3000.0, "A", 9], [30.0, 4000.0, "B", None],
                           [25.0, 3500.0, "C", 3.5], [None, 2000.0, "D", 3],
                           [22.0, 2500.0]]}
        s, v, sw, vw = self._pair(tmp_path, plot)
        assert _glyphs(s) == _glyphs(v) and _glyphs(s)
        assert _all_labels(s) == _all_labels(v)
        assert [t for (_, _, t, _, _) in _all_labels(s)] == \
            [("A",), ("C",), ("B",)]
        assert _notes(sw, "scatteri") == _notes(vw, "scatteri")
        assert len(_notes(sw, "clock")) == 1

    def test_pci_with_labels_clocks_and_a_missing_coordinate(self, tmp_path):
        plot = {"type": "pci", "options": {"lcolor": "maroon"},
                "values": [[20.0, 3000.0, 30.0, 4000.0, "A", 3],
                           [25.0, 2000.0, 22.0, 3500.0],
                           [None, 1.0, 2.0, 3.0, "B", None]]}
        s, v, sw, vw = self._pair(tmp_path, plot)
        assert _glyphs(s) == _glyphs(v)
        assert _glyphs(s) == [("Segment", {"x0": [3000.0, 2000.0],
                                           "y0": [20.0, 25.0],
                                           "x1": [4000.0, 3500.0],
                                           "y1": [30.0, 22.0]})]
        assert _all_labels(s) == _all_labels(v) == []
        assert _notes(sw, "pci") == _notes(vw, "pci")

    def test_pcarrowi_with_an_odd_clock_position(self, tmp_path):
        plot = {"type": "pcarrowi", "options": {},
                "values": [[20.0, 3000.0, 30.0, 4000.0, "A", 3.5],
                           [25.0, 2000.0, 22.0, 3500.0, "B", 6]]}
        s, v, sw, vw = self._pair(tmp_path, plot)
        assert _all_labels(s) == _all_labels(v)
        # WP-30 P1.12a (Evidence E5, twoway measured): pcarrow's origin is
        # half the scheme marker size, 2.93334 + gap 2.66667 = 5.6 px.
        assert [(dx, dy) for (dx, dy, _, _, _) in _all_labels(s)] == \
            [(0, -_D), (0, _D)]
        assert _notes(sw, "pcarrowi") == _notes(vw, "pcarrowi")
        assert len(_notes(sw, "clock")) == 1

    def test_a_scatteri_label_reaches_the_served_page_as_text(self, tmp_path):
        """The label is data in the served document, drawn at its clock
        position, whatever it holds."""
        payload = "</script><script>alert(1)</script>{bf:X}"
        spec = make_spec([{"type": "scatteri", "options": {},
                           "values": [[1.0, 2.0, payload, 9]]}])
        doc = _session(_load_app(_app_source(tmp_path, spec),
                                 "imm_%d" % next(_SEQ)))
        got = [(round(ls.x_offset, 4), round(ls.y_offset, 4),
                list(ls.source.data[_text_field(ls)]))
               for ls in doc.select({"type": LabelSet})]
        # WP-30 P1.12a (Evidence E5, twoway measured): 9 o'clock is
        # -(radius + default gap), -(2.93334 + 2.66667) px.
        # Flipped (WP-30 P1.11b): {bf:X} is graph-text markup, which twoway
        # draws as the bold text; the label stays text, never HTML or
        # script.
        assert got == [(-_D, 0, [payload.replace("{bf:X}", "X")])]
