#!/usr/bin/env python3
"""Extract Stata's colour table from its own style files.

Stata defines every named colour in ``<ado>/base/style/color-<name>.style``
as a ``set rgb "R G B"`` line.  Those files are the authority: a name's
appearance in a Stata graph is whatever that file says, and nothing else.

Usage::

    python3 scripts/extract_color_truth.py            # default Stata location
    python3 scripts/extract_color_truth.py /path/to/ado/base/style

Writes ``test/fixtures/color_truth.json`` so the fidelity test can run on a
machine with no Stata installed.
"""
import datetime
import glob
import json
import os
import re
import sys

_DEFAULT_STYLE_DIRS = (
    "/Applications/StataNow/ado/base/style",
    "/Applications/Stata/ado/base/style",
    "/usr/local/stata/ado/base/style",
)

_RGB = re.compile(r'set\s+rgb\s+"\s*(\d+)\s+(\d+)\s+(\d+)\s*"')
_LABEL = re.compile(r'^\*\s*label\s+"([^"]*)"', re.M)


def _style_dir(argv):
    if len(argv) > 1:
        return argv[1]
    for d in _DEFAULT_STYLE_DIRS:
        if os.path.isdir(d):
            return d
    raise SystemExit(
        "could not find Stata's style directory; pass it as an argument")


def main(argv):
    style_dir = _style_dir(argv)
    colors = {}
    for path in sorted(glob.glob(os.path.join(style_dir, "color-*.style"))):
        name = os.path.basename(path)[len("color-"):-len(".style")]
        text = open(path, encoding="utf-8", errors="replace").read()
        m = _RGB.search(text)
        if not m:
            # A few style files alias another colour rather than setting rgb;
            # they are recorded as aliases, not invented.
            continue
        r, g, b = (int(x) for x in m.groups())
        label = _LABEL.search(text)
        colors[name] = {
            "hex": "#%02x%02x%02x" % (r, g, b),
            "rgb": [r, g, b],
            "label": label.group(1) if label else "",
            "source": os.path.basename(path),
        }

    out = {
        "_meta": {
            "generated_utc": datetime.datetime.now(
                datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "style_dir": style_dir,
            "n_colors": len(colors),
            "note": (
                "Every entry is the `set rgb' line of Stata's own "
                "color-<name>.style file. These are the colours Stata draws; "
                "dash's _COLOR_MAP must agree with them exactly."
            ),
        },
        "colors": colors,
    }
    dest = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "test", "fixtures", "color_truth.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("wrote %s (%d colours)" % (dest, len(colors)))


if __name__ == "__main__":
    main(sys.argv)
