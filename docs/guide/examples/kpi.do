* KPI cards: one statistic each, formatted, and recomputed when the
* filters move.
sysuse nlsw88, clear
dash clear
dash kpi count(idcode), title("Women") name(n) fmt(%9.0fc)
dash kpi mean(wage), title("Mean hourly wage") name(wage) fmt(%9.2f) ///
    subtitle("dollars")
dash kpi median(hours), title("Median hours") name(hours) ///
    subtitle("per week")
dash kpi mean(union), title("Union members") name(union) fmt(%9.2f) ///
    subtitle("share of those asked") color(white) bgcolor(navy)
dash scatter wage ttl_exp, name(exp) title("Wage and experience") ///
    hover(occupation)
dash build, saving(kpi.html, replace) filter(race) filter(collgrad) ///
    layout(bs: n=3 wage=3 hours=3 union=3 / exp=12) ///
    title("NLSW 1988")
