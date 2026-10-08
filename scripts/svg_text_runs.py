"""scripts/svg_text_runs.py -- WP-30 P1.11b: the styled runs of each
``<text>`` in a Stata-exported twoway SVG.

WHY THIS EXISTS

dash draws Stata's graph-text markup (``{bf:}``, ``{it:}``, ``{sup:}``,
``{&alpha}``, ``{c 233}`` ...) as twoway draws it, and the proof is what
twoway's own SVG export writes.  ``scripts/svg_truth.py``'s
``svg_document`` keeps a ``<text>`` element's inner markup in its text and
is HIGH-impact, so this reader is its sibling, not an edit of it.

WHAT STATA'S WRITER EMITS (StataNow 19.5, measured 08oct2026)

* A text drawn in one style is ``<text style="font-family:'Helvetica';
  font-size:..px;fill:..">text</text>``.
* A text with several styles is a ``<text>`` holding one ``<tspan>`` per
  run, each with its own ``style`` (``font-weight:bold``,
  ``font-style:italic``, ``font-family:'Times'``, ``font-size``), with
  layout whitespace between the tspans.
* A raised or lowered run carries ``dy`` (``{sup:}`` -58.96px, then a
  following ``{sub:}`` +75.04px at a 112.56px tick label): the running
  sum of ``dy`` below zero is raised, above zero lowered.
* A control code ``{c 1}`` is written as the raw character; ``&`` and
  ``<`` as entities; a run of spaces as U+00A0.

RULES: stdlib only (``re``, ``html``); never imports Stata or calls it
back; a ``python:`` block importing this module spells a backtick
``\\x60``.
"""

import html
import re

_RE_TEXT = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)
_RE_TSPAN = re.compile(r"<tspan\b([^>]*)>(.*?)</tspan>", re.S)
_RE_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
_RE_ENTITY = re.compile(
    r"&(#[0-9]{1,7}|#x[0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]{0,31});")


def _entity(m):
    body = m.group(1)
    if body.startswith("#x"):
        n = int(body[2:], 16)
    elif body.startswith("#"):
        n = int(body[1:])
    else:
        return html.unescape(m.group(0))
    if n > 0x10FFFF:
        return m.group(0)
    return chr(n)


def _decode(s):
    """Entities decoded once (a numeric reference to its code point, even a
    control code, which ``html.unescape`` would drop or remap); U+00A0 to a
    space; raw control characters kept."""
    return _RE_ENTITY.sub(_entity, s).replace(" ", " ")


def _style(attr_text):
    a = dict(_RE_ATTR.findall(attr_text))
    out = {}
    for part in a.get("style", "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip()
    return a, out


def _num(s):
    try:
        return float(str(s).replace("px", ""))
    except (TypeError, ValueError):
        return None


def _run(text, own, inherited, shift):
    st = dict(inherited)
    st.update(own)
    size = _num(st.get("font-size"))
    return {
        "text": _decode(text),
        "weight": "bold" if st.get("font-weight") == "bold" else "normal",
        "style": "italic" if st.get("font-style") == "italic" else "normal",
        "family": st.get("font-family", "").strip("'\""),
        "size": size,
        "level": "sup" if shift < -0.5 else ("sub" if shift > 0.5 else ""),
    }


def svg_text_runs(path):
    """One dict per ``<text>`` of the SVG at *path*, in document order:
    ``{"x", "y", "runs"}``, each run ``{"text", "weight", "style",
    "family", "size", "level"}`` (level ``"sup"``, ``"sub"`` or ``""``).
    Raises ``FileNotFoundError`` for a missing file."""
    with open(path, encoding="utf-8") as fh:
        doc = fh.read()
    out = []
    for m in _RE_TEXT.finditer(doc):
        attrs, own = _style(m.group(1))
        body = m.group(2)
        runs = []
        spans = list(_RE_TSPAN.finditer(body))
        if spans:
            shift = 0.0
            for t in spans:
                ta, tst = _style(t.group(1))
                dy = _num(ta.get("dy"))
                if dy is not None:
                    shift += dy
                runs.append(_run(t.group(2), tst, own, shift))
        else:
            runs.append(_run(body, {}, own, 0.0))
        out.append({"x": _num(attrs.get("x")), "y": _num(attrs.get("y")),
                    "runs": runs})
    return out
