* Image panels: put an SVG -- here a graph Stata drew -- beside dash's
* graphs.
sysuse auto, clear
dash clear
twoway scatter mpg weight, title("Drawn by Stata")
graph export stata-scatter.svg, replace
dash image using stata-scatter.svg, name(stata) ///
    caption("Stata's graph, exported as SVG")
dash scatter mpg weight, name(live) title("Drawn by dash")
dash build, saving(image-panel.html, replace) layout(1 2) ///
    title("An image beside a graph")
