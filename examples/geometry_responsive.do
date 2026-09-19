*! geometry_responsive.do
*! The geometry exemplar: KPIs, graphs of three different shapes, and a
*! faceted graph, under layout(bs).
*!
*! Used by test/test_geometry_visual.md.  Before S10 no figure in any
*! generated dashboard carried a width, height, frame_width or aspect_ratio
*! -- 67 Figure objects across 10 dashboards, every one at
*! sizing_mode="stretch_width" and Bokeh's default height.  There was no way,
*! by option, by scheme or by data, to influence plot proportions.

clear all
sysuse auto, clear
dash clear

dash kpi count(mpg),   name(k1) title("Cars")        fmt(%9.0fc)
dash kpi mean(mpg),    name(k2) title("Mean MPG")    fmt(%9.1f)
dash kpi mean(price),  name(k3) title("Mean price")  fmt(%9.0fc)
dash kpi max(weight),  name(k4) title("Max weight")  fmt(%9.0fc)

// A wide panel: 10 x 2 inches
dash scatter mpg weight, name(wide) xsize(10) ysize(2) ///
    title("Wide (xsize 10, ysize 2)") xtitle("Weight") ytitle("MPG")

// A square panel
dash scatter price weight, name(square) aspectratio(1) ///
    title("Square (aspectratio 1)") xtitle("Weight") ytitle("Price")

// Scheme default proportions
dash scatter mpg length, name(scheme) ///
    title("Scheme default proportions") xtitle("Length") ytitle("MPG")

// A faceted graph: panels must match the unfaceted ones
dash scatter mpg weight, name(faceted) by(foreign) ///
    title("Faceted by origin") xtitle("Weight") ytitle("MPG")

dash build,                                            ///
    saving("geometry_responsive.html")                 ///
    title("Geometry & responsiveness")                 ///
    subtitle("KPIs, three shapes, and a faceted graph") ///
    layout(bs)                                         ///
    replace
