* brush(filter): a selection hides the cars it leaves out, and the KPI
* cards count and summarize the selection.
sysuse auto, clear
dash clear
dash kpi count(make), title("Cars selected") name(n) update(brush)
dash kpi mean(price), title("Mean price") name(p) fmt(%9.0fc) update(brush)
dash scatter mpg weight, name(g1) title("Mileage and weight") hover(make)
dash scatter price length, name(g2) title("Price and length") hover(make)
dash build, saving(brush-filter.html, replace) link(g1 g2) brush(filter) ///
    layout(bs: n=6 p=6 / g1=6 g2=6) title("Brushing that filters")
