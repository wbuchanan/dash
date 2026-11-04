"""The known differences of dash's plot region under scale() from twoway's
(WP-33 section 33-11, GW-11; test/known_differences.py's rule, D-33-10.a).

Keys are ``"<command>:<side>:<check>"``: command A (``twoway scatter mpg
weight, title("T")``) or B (scatter and lfit with title, subtitle, ytitle,
xtitle and note), side top, left, bottom or right, and check ``slope``,
``intercept`` or ``linear`` of the side's inset (CSS px) fitted against
scale()'s factor over 0.5, 0.75, 1, 1.5 and 2 (D-33-11.e).  Each value is
the GAPS4 item that fixes the difference; the comment gives twoway's and
dash's measured numbers (Chrome, 528 px wide, 21oct2026) and the ruling
(D43, the maintainer's of 21oct2026).

``SCALE_FRAME_TWOWAY_KNOWN`` lists where twoway's own inset is not linear
in the factor (D43: under scale(2) command B's legend is wider than the
plot, and twoway widens the plot column leftward); its owner is the item
whose fix must match it.  test/test_sizing.py::TestScaleFrameTruth checks
both tables' rows are live; test/test_scale_frame.py (release tier) checks
the comparison against SCALE_FRAME_KNOWN.
"""

# WP-43 LT-6 (batch 43.4) drew the legend's style(), size, offset,
# showindex and region styles; these legend-widening rows under scale()
# are none of them, so they stay as LT-6 (residual) until the item that
# draws twoway's widening takes them (reported to the orchestrator).
SCALE_FRAME_KNOWN = {
    "A:bottom:intercept": "GW-6 (residual)",  # D43: twoway 13.44 / dash 5.72 px
    "A:left:intercept": "GW-6 (residual)",  # D43: twoway 13.44 / dash 5.72 px
    "A:right:intercept": "GW-6 (residual)",  # D43: twoway 13.46 / dash 5.00 px
    "A:top:intercept": "GW-6 (residual)",  # D43: twoway 13.44 / dash -0.96 px
    "A:top:slope": "VF-4 (residual)",  # D43: twoway 23.28 / dash 32.31 px per unit
    "B:bottom:intercept": "GW-6 (residual)",  # D43: twoway 13.44 / dash 6.20 px
    "B:bottom:linear": "LT-6 (residual)",  # D43: twoway residual 0.01 / dash 2.93 px
    "B:left:intercept": "GW-6 (residual)",  # D43: twoway 19.23 / dash 5.72 px
    "B:left:slope": "LT-6 (residual)",  # D43: twoway 31.50 (legend widens) / dash 36.41
    "B:right:intercept": "GW-6 (residual)",  # D43: twoway 13.46 / dash 5.00 px
    "B:top:intercept": "GW-6 (residual)",  # D43: twoway 13.44 / dash -0.97 px
    "B:top:slope": "VF-4 (residual)",  # D43: twoway 42.55 / dash 59.45 px per unit
}

SCALE_FRAME_DELIBERATE = {}

SCALE_FRAME_TWOWAY_KNOWN = {
    "B:left:linear": "LT-6 (residual)",  # D43: twoway's residual 37 SVG units at k=2
}
