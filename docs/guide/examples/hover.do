* Tooltips: hover() adds variables to what a point's tooltip shows.
sysuse auto, clear
dash scatter mpg weight, hover(make price foreign) ///
    title("Point at a car") saving(hover.html, replace)
