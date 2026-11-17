* Linked brushing: a box or lasso selection on one graph highlights the
* same cars on every graph in the link group.
sysuse auto, clear
dash clear
dash scatter mpg weight, name(weight) title("Mileage and weight") hover(make)
dash scatter price mpg, name(price) title("Price and mileage") hover(make)
dash histogram length, name(length) title("Length")
dash build, saving(linked.html, replace) link(weight price length) ///
    layout(1 3) title("Linked brushing") ///
    subtitle("Choose Box select, then drag across any graph")
