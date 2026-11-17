* Data tables: table puts the rows a graph draws under it, and csv adds a
* Download CSV button.
sysuse auto, clear
dash clear
dash scatter mpg weight, name(cars) title("Mileage and weight") ///
    hover(make price) table(rows(20) open)
dash build, saving(tables.html, replace) filter(foreign) csv ///
    title("Data tables")
