* Filters: the four widget types in a sidebar, and a filter one card ignores.
sysuse nlsw88, clear
dash clear
dash kpi mean(wage), title("Mean wage") name(mw) fmt(%9.2f)
dash kpi count(idcode), title("Women in the data") name(all) fmt(%9.0fc)
dash scatter wage ttl_exp, name(g1) title("Wage and experience")
dash histogram wage, name(g2) title("Wages")
dash build, saving(filters.html, replace) ///
    filter(race) ///
    filter(occupation, type(multi)) ///
    filter(age, type(range)) ///
    filter(grade, type(slider) label("Years of school, at least") exclude(all)) ///
    filterposition(left) layout(bs: mw=6 all=6 / g1=6 g2=6) title("Filters")
