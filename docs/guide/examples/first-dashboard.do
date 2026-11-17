* A first dashboard: register graphs with name(), then build one page.
sysuse auto, clear
dash clear
dash scatter mpg weight, name(fuel) title("Mileage and weight")
dash histogram price, name(prices) title("Prices")
dash build, saving(first-dashboard.html, replace) layout(1 2) ///
    title("1978 automobiles") subtitle("Two graphs on one page")
