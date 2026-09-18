"""
conftest.py — Shared pytest fixtures for the dash test suite.

Centralises commonly-used fixtures so individual test files don't each
define their own copy of auto_df, make_spec, make_dr, etc.
"""
import sys
import os
import json
import tempfile

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

from dash_render import DashRenderer, GlyphMapper, OptionTranslator, SchemeParser


# ============================================================
# Environment pinning
# ============================================================
# The pytest suite and the Stata certification suite run under DIFFERENT
# Python interpreters, with different library versions:
#
#   pytest        /opt/homebrew/bin/python3.14
#   Stata's       /opt/anaconda3/bin/python3   (set python_exec)
#
# A green pytest run therefore does NOT prove the Stata path works, and a
# library difference between them can make a defect reproduce in one and not
# the other.  This fixture records what pytest actually ran under and warns
# when it drifts from the values captured in .ultraplan/BASELINE.md.
#
# A warning, not a failure: a developer on another machine is legitimately on
# a different build.  But it is never silent.

_BASELINE_ENV = {
    "python": "3.14",       # major.minor only — patch drift is not interesting
    "bokeh": "3.9",
    "pandas": "3.0",
    "numpy": "2.4",
    "scipy": "1.17",
}


def _mm(version: str) -> str:
    """Return the major.minor prefix of a version string."""
    parts = str(version).split(".")
    return ".".join(parts[:2])


@pytest.fixture(scope="session", autouse=True)
def pinned_environment():
    """Warn when the interpreter or its libraries drift from the baseline."""
    import importlib
    import warnings

    actual = {"python": _mm("%d.%d" % sys.version_info[:2])}
    for pkg in ("bokeh", "pandas", "numpy", "scipy"):
        try:
            actual[pkg] = _mm(importlib.import_module(pkg).__version__)
        except Exception:
            actual[pkg] = "missing"

    drifted = {
        k: (v, actual[k]) for k, v in _BASELINE_ENV.items() if actual[k] != v
    }
    if drifted:
        detail = ", ".join(
            f"{k}: baseline {want}, running {got}" for k, (want, got) in drifted.items()
        )
        warnings.warn(
            "dash test suite: environment differs from the recorded baseline "
            f"({detail}). See .ultraplan/BASELINE.md. Results may not be "
            "comparable to it, and the Stata certification suite runs under a "
            "different interpreter again (/opt/anaconda3/bin/python3).",
            UserWarning,
        )
    return actual


# ============================================================
# Core dataset fixture
# ============================================================

@pytest.fixture
def auto_df():
    """Synthetic 74-row dataset mimicking Stata's auto.dta.

    Used across GlyphMapper, filter, KPI, and pipeline tests.
    Seed is fixed so tests are deterministic.
    """
    np.random.seed(42)
    n = 74
    return pd.DataFrame({
        "mpg":    np.random.randint(12, 40, n).astype(float),
        "weight": np.random.randint(1760, 4840, n).astype(float),
        "price":  np.random.randint(3291, 15906, n).astype(float),
        "length": np.random.randint(142, 233, n).astype(float),
        "foreign": np.random.choice([0, 1], n).astype(float),
        "rep78":   np.random.choice([1.0, 2.0, 3.0, 4.0, 5.0, np.nan], n),
    })


# ============================================================
# Bokeh primitives
# ============================================================

@pytest.fixture
def cds(auto_df):
    """ColumnDataSource built from the synthetic auto DataFrame."""
    return ColumnDataSource(auto_df)


@pytest.fixture
def fig():
    """Blank Bokeh Figure suitable for mapper tests."""
    return figure()


@pytest.fixture
def gm():
    """Default GlyphMapper instance (s2color scheme)."""
    scheme = SchemeParser("s2color")
    return GlyphMapper(OptionTranslator(), scheme)


# ============================================================
# DashRenderer helpers
# ============================================================

def make_spec(
    plots: list,
    *,
    link: str = "",
    filters: "list | None" = None,
    hover: str = "",
    graph_name: str = "g1",
    theme: str = "default",
    extra_graphs: "list | None" = None,
    kpis: "list | None" = None,
) -> dict:
    """Build a minimal DashRenderer spec dict from a list of plot dicts.

    Args:
        plots:         List of plot spec dicts (type, yvar, xvar, options).
        link:          Link spec string, e.g. ``"g1"`` or ``"_all"``.
        filters:       List of filter spec dicts for build_options.filters.
        hover:         Space-separated hover variable list for graph_options.
        graph_name:    Name for the single graph (default ``"g1"``).
        theme:         Bokeh scheme name (default ``"default"``).
        extra_graphs:  Additional graph specs to include alongside the main one.
        kpis:          List of KPI spec dicts.

    Returns:
        A dict conforming to the DashRenderer spec format.
    """
    go: dict = {"name": graph_name}
    if hover:
        go["hover"] = hover

    graphs = [{"plots": plots, "graph_options": go,
                "if_expr": "", "in_expr": ""}]
    if extra_graphs:
        graphs.extend(extra_graphs)

    build: dict = {
        "layout": "auto",
        "link": link,
        "theme": theme,
        "title": "",
        "subtitle": "",
        "registry": graph_name,
    }
    if filters:
        build["filters"] = filters

    return {
        "graphs": graphs,
        "kpis": kpis or [],
        "build_options": build,
    }


def make_data_json(
    df: pd.DataFrame,
    value_labels: "dict | None" = None,
    value_label_names: "dict | None" = None,
) -> dict:
    """Serialise a DataFrame to the StataJSON wrapper dict.

    Args:
        df:               DataFrame whose columns become variableNames.
        value_labels:     Optional ``{labelset: {code: text}}`` mapping.
        value_label_names: Optional ``{varname: labelset}`` mapping.

    Returns:
        A ``{"StataJSON": {...}}`` dict suitable for writing to a data JSON file.
    """
    varnames = list(df.columns)
    values = []
    for _, row in df.iterrows():
        entry: dict = {}
        for col in varnames:
            val = row[col]
            entry[col] = None if (isinstance(val, float) and np.isnan(val)) else val
        values.append(entry)

    return {"StataJSON": {
        "variableNames": varnames,
        "variableLabels": {v: v for v in varnames},
        "valueLabels": value_labels or {},
        "valueLabelNames": value_label_names or {},
        "variableTypeIsString": {v: False for v in varnames},
        "values": values,
    }}


def make_dr(
    plots: list,
    df: "pd.DataFrame | None" = None,
    *,
    link: str = "",
    filters: "list | None" = None,
    hover: str = "",
    graph_name: str = "g1",
    value_labels: "dict | None" = None,
    value_label_names: "dict | None" = None,
    render: bool = True,
) -> DashRenderer:
    """Build (and optionally render) a DashRenderer from inline Python data.

    Args:
        plots:        List of plot spec dicts.
        df:           DataFrame for the data file.  Defaults to a small
                      synthetic 10-row auto-like dataset when ``None``.
        link:         Link spec for build_options.
        filters:      Filter specs for build_options.filters.
        hover:        Hover variable string for graph_options.hover.
        graph_name:   Graph name (default ``"g1"``).
        value_labels: Optional value-label mapping.
        value_label_names: Optional variable→labelset mapping.
        render:       If ``True`` (default) call ``dr.render()`` before
                      returning.

    Returns:
        A DashRenderer instance (rendered if *render* is True).
    """
    if df is None:
        np.random.seed(42)
        n = 10
        df = pd.DataFrame({
            "mpg":    np.linspace(15, 35, n),
            "weight": np.linspace(2000, 4000, n),
            "price":  np.linspace(4000, 12000, n),
            "foreign": [0.0, 1.0] * (n // 2),
        })

    spec = make_spec(
        plots, link=link, filters=filters, hover=hover, graph_name=graph_name
    )
    data = make_data_json(df, value_labels=value_labels,
                          value_label_names=value_label_names)

    sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
    try:
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(data, f)
        dr = DashRenderer(sp, dp, op)
        if render:
            dr.render()
    finally:
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass
    return dr
