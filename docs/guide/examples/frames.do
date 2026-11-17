* Graphs from several frames: each graph is drawn from the frame it was
* registered in.
dash clear
capture frame drop cars
capture frame drop stocks
frame create cars
frame cars: sysuse auto, clear
frame create stocks
frame stocks: sysuse sp500, clear
frame cars: dash scatter mpg weight, name(cars) title("Cars (auto)")
frame stocks: dash line close date, name(stocks) title("S&P 500 close (sp500)")
dash build, saving(frames.html, replace) layout(1 2) ///
    title("Two datasets, one page")
