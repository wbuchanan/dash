* Tabs: tabs() groups graphs and cards, each tab with its own layout.
sysuse auto, clear
dash clear
dash kpi mean(mpg), title("Mean MPG") name(k1) fmt(%9.1f)
dash kpi mean(price), title("Mean price") name(k2) fmt(%9.0fc)
dash scatter mpg weight, name(s1) title("Mileage and weight")
dash scatter mpg length, name(s2) title("Mileage and length")
dash histogram mpg, name(h1) title("Mileage")
dash build, saving(tabs.html, replace) ///
    tabs(Overview: k1 k2 s1, layout(k1:1,1 k2:1,2 s1:2,1) / Detail: s2 h1) ///
    title("Tabs")
