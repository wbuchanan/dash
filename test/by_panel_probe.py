"""
by_panel_probe.py -- find a by() graph's panels and its overall text the way
the page draws them (WP-30 P1.15a).

A by() panel used to be found by its title, which held the panel label
(``"T — Domestic"``).  twoway keeps the graph's title() on every panel and
draws the label as a row of its own, so the title no longer tells panels
apart: a panel is found by its label ``Title`` (named ``dash_by_label``),
and the graph's overall text lives in two chrome cells of the panel grid
(bare ``Plot`` models named ``dash_by_head`` and ``dash_by_foot``), which
are not panels.  Every test that looks for a panel uses these helpers.

WP-30 P1.15c adds the side cells -- the axis-title cells, the overall
legend, the colour key and the stacked view's ruler -- also bare
``Plot``s named ``dash_by_*``; none is a panel.
"""

CHROME_NAMES = ("dash_by_head", "dash_by_foot")
SIDE_NAMES = ("dash_by_ytitle", "dash_by_xtitle", "dash_by_legend",
              "dash_by_clegend", "dash_by_ruler",
              # WP-41 BY-14: by(, plegend())'s cell.
              "dash_by_plegend",
              # WP-41 BY-12: by()'s edge-title columns.
              "dash_by_l2title", "dash_by_r1title", "dash_by_r2title")


def panel_label_title(fig):
    """The panel's label ``Title``, or None."""
    for m in list(getattr(fig, "above", []) or []) + \
            list(getattr(fig, "below", []) or []):
        if type(m).__name__ == "Title" and \
                getattr(m, "name", None) == "dash_by_label":
            return m
    return None


def panel_label(fig):
    """The text of the panel's label row, ``""`` when it has none."""
    t = panel_label_title(fig)
    return str(t.text or "") if t is not None else ""


def is_chrome(model):
    """Whether *model* is a by() grid's chrome cell: its head or foot, or
    (WP-30 P1.15c) a title, legend or key cell beside the panels."""
    return getattr(model, "name", None) in CHROME_NAMES + SIDE_NAMES


def is_side(model):
    """Whether *model* is a by() grid's title, legend or key cell
    (WP-30 P1.15c)."""
    return getattr(model, "name", None) in SIDE_NAMES


def side_title(cell):
    """``(letter, text)`` of a by() title cell (WP-30 P1.15c: twoway's
    l1title and b1title, drawn once left of and below the panels, in
    ``dash_by_ytitle`` and ``dash_by_xtitle``): *letter* is ``"y"`` or
    ``"x"``; None for any other model."""
    letter = {"dash_by_ytitle": "y", "dash_by_xtitle": "x"}.get(
        getattr(cell, "name", None))
    if letter is None:
        return None
    side = "left" if letter == "y" else "below"
    texts = [str(m.text or "") for m in getattr(cell, side)
             if type(m).__name__ == "Title"]
    return letter, (texts[0] if texts else "")


def grid_cells(roots):
    """Every by() grid under *roots* (a ``GridPlot`` with a labelled
    panel; a dashboard's own grid is not one) as the list of its cells'
    models -- panels, chrome and side cells -- in child order."""
    from bokeh.models import GridPlot
    out, seen = [], set()
    for root in roots:
        for m in root.references():
            if not isinstance(m, GridPlot) or m.id in seen:
                continue
            seen.add(m.id)
            cells = [c[0] for c in m.children]
            if any(panel_label_title(c) is not None for c in cells):
                out.append(cells)
    return out


def chrome_texts(cell):
    """A chrome cell's text rows in reading order: its title, its above
    rows from the outermost in, its in-band Labels, then its below rows."""
    out = []
    title = getattr(cell, "title", None)
    if title is not None and str(title.text or ""):
        out.append(str(title.text))
    rows = [m for m in reversed(list(cell.above))
            if type(m).__name__ == "Title"]
    rows += [m for m in cell.center if type(m).__name__ == "Label"]
    rows += [m for m in cell.below if type(m).__name__ == "Title"]
    out += [str(m.text) for m in rows if str(m.text or "")]
    return out


def by_grid(root):
    """``(panels, head, foot)`` of the one by() GridPlot under *root*:
    ``panels`` is ``[(row, col, fig)]`` re-based so the first panel row and
    column are 0 (the side cells skipped), sorted by place; *head*/*foot* the chrome cells or None."""
    from bokeh.models import GridPlot
    grids = [m for m in root.references() if isinstance(m, GridPlot)
             and any(type(c[0]).__name__ == "figure" for c in m.children)]
    assert len(grids) == 1, "expected one panel grid, found %d" % len(grids)
    head = foot = None
    panels = []
    for child in grids[0].children:
        model, row, col = child[0], int(child[1]), int(child[2])
        if getattr(model, "name", None) == "dash_by_head":
            head = model
        elif getattr(model, "name", None) == "dash_by_foot":
            foot = model
        elif is_side(model):
            continue
        else:
            panels.append((row, col, model))
    base = min((r for r, _, _ in panels), default=0)
    cbase = min((c for _, c, _ in panels), default=0)
    panels = sorted(((r - base, c - cbase, f) for r, c, f in panels),
                    key=lambda t: (t[0], t[1]))
    return panels, head, foot


def find_panel(figs, label):
    """The one figure of *figs* whose label row reads *label*."""
    hits = [f for f in figs if panel_label(f) == label]
    assert len(hits) == 1, "no single panel %r among %r" % (
        label, [panel_label(f) for f in figs])
    return hits[0]
