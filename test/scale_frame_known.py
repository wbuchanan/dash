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
# WP-45 GW-6 (08nov2026): the comparison reads the graph region box, the
# scheme's margin drawn round the figure, so A:top, B:left and B:top's
# intercepts agree and their rows are gone; the other intercepts are
# Bokeh's own 5 px border inside the margin (GW-6's residual), gone
# since every figure's min_border is 0 (WP-45 GW-6, 08nov2026): the
# A:right and B:right intercept rows too (15.00 px against 13.46: the
# margin and the plot region outline's 1 px).  The
# A:bottom, A:left and B:bottom intercepts did not move (an axis side's
# border was never Bokeh's 5 px): an axis's room extrapolated to
# scale(0) keeps about 5 px twoway's does not, the residual BUGS.md
# "An axis's room under scale() keeps about 5 px that twoway's does not".
# WP-45 VF-4 residual (08nov2026): each title-family box takes twoway's
# room, its size plus its style's margin (_dash_title_standoffs), so
# A:top and B:top's slopes agree and their rows are gone.
SCALE_FRAME_KNOWN = {
    "A:bottom:intercept": "GW-6 (residual)",  # twoway 13.44 / dash 19.72 px (08nov2026)
    "A:left:intercept": "GW-6 (residual)",  # twoway 13.44 / dash 18.72 px (08nov2026)
    "B:bottom:intercept": "GW-6 (residual)",  # twoway 13.44 / dash 21.16 px (08nov2026)
    "B:bottom:linear": "LT-6 (residual)",  # D43: twoway residual 0.01 / dash 2.86 px
    "B:left:slope": "LT-6 (residual)",  # D43: twoway 31.50 (legend widens) / dash 36.41
}

SCALE_FRAME_DELIBERATE = {}

SCALE_FRAME_TWOWAY_KNOWN = {
    "B:left:linear": "LT-6 (residual)",  # D43: twoway's residual 37 SVG units at k=2
}
