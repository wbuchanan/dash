*! sp500_dates.do
*! The date exemplar: a %td x-axis, KPIs over a date variable, and a date
*! range filter.
*!
*! Until S08 this dashboard was EMPTY.  jsonio renders a %t* variable through
*! its display format and emits a JSON string ("02jan2001") while still
*! reporting variableIsString=false, so the renderer coerced every date to
*! missing and dropped every row: `dash line close date` produced a dashboard
*! containing zero data points and returned rc 0.  dash now transports the
*! underlying value and carries the display format separately.

clear all
sysuse sp500, clear
dash clear

dash kpi min(date),   name(k1) title("First trading day")
dash kpi max(date),   name(k2) title("Last trading day")
dash kpi max(close),  name(k3) title("Peak close")  fmt(%9.2f)
dash kpi mean(volume), name(k4) title("Mean volume") fmt(%9.0fc)

dash line close date, name(g1) title("Closing price") ///
    xtitle("Date") ytitle("Close")

dash line volume date, name(g2) title("Volume") ///
    xtitle("Date") ytitle("Volume (thousands)")

dash build,                                        ///
    saving("sp500_dates.html")                     ///
    title("S&P 500, 2001")                         ///
    subtitle("Closing price and volume")           ///
    layout(bs: k1=3 k2=3 k3=3 k4=3 / g1=12 / g2=12) ///
    filter(date, type(range))                      ///
    link(_all)                                     ///
    replace
