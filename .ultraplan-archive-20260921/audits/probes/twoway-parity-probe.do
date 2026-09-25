clear all
adopath ++ "/Users/billy/Desktop/Programs/Java/StataJSON"
adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
sysuse auto, clear
gen double t = _n
set more off
dash clear
capture dash scatter mpg weight, xsize(6) name(g0)
di "RESULT|000|rc=" _rc
dash clear
capture dash scatter mpg weight, ysize(4) name(g1)
di "RESULT|001|rc=" _rc
dash clear
capture dash scatter mpg weight, text(30 3000 "hi") name(g2)
di "RESULT|002|rc=" _rc
dash clear
capture dash scatter mpg weight, xtick(2000(500)4000) name(g3)
di "RESULT|003|rc=" _rc
dash clear
capture dash scatter mpg weight, xmlabel(2500 3500) name(g4)
di "RESULT|004|rc=" _rc
dash clear
capture dash scatter mpg weight, sort name(g5)
di "RESULT|005|rc=" _rc
dash clear
capture dash scatter mpg weight, mlwidth(thin) name(g6)
di "RESULT|006|rc=" _rc
dash clear
capture dash scatter mpg weight, mstyle(p1) name(g7)
di "RESULT|007|rc=" _rc
dash clear
capture dash scatter mpg weight, lstyle(p1) name(g8)
di "RESULT|008|rc=" _rc
dash clear
capture dash bar mpg weight, horizontal name(g9)
di "RESULT|009|rc=" _rc
dash clear
capture dash histogram mpg, bin(20) name(g10)
di "RESULT|010|rc=" _rc
dash clear
capture dash histogram mpg, width(2) name(g11)
di "RESULT|011|rc=" _rc
dash clear
capture dash histogram mpg, percent name(g12)
di "RESULT|012|rc=" _rc
dash clear
capture dash histogram mpg, frequency name(g13)
di "RESULT|013|rc=" _rc
dash clear
capture dash histogram mpg, density name(g14)
di "RESULT|014|rc=" _rc
dash clear
capture dash histogram mpg, start(10) name(g15)
di "RESULT|015|rc=" _rc
dash clear
capture dash kdensity mpg, kernel(epanechnikov) name(g16)
di "RESULT|016|rc=" _rc
dash clear
capture dash kdensity mpg, bwidth(2) name(g17)
di "RESULT|017|rc=" _rc
dash clear
capture dash kdensity mpg, n(100) name(g18)
di "RESULT|018|rc=" _rc
dash clear
capture dash lfitci mpg weight, level(90) name(g19)
di "RESULT|019|rc=" _rc
dash clear
capture dash lowess mpg weight, bwidth(.6) name(g20)
di "RESULT|020|rc=" _rc
dash clear
capture dash lpoly mpg weight, degree(1) name(g21)
di "RESULT|021|rc=" _rc
dash clear
capture dash function y=x**2, range(0 10) name(g22)
di "RESULT|022|rc=" _rc
dash clear
capture dash function y=x**2, n(400) name(g23)
di "RESULT|023|rc=" _rc
dash clear
capture dash scatter mpg weight, nodraw name(g24)
di "RESULT|024|rc=" _rc
dash clear
capture dash scatter mpg weight, play(x) name(g25)
di "RESULT|025|rc=" _rc
dash clear
capture dash scatter mpg weight, title("T", size(large)) name(g26)
di "RESULT|026|rc=" _rc
dash clear
capture dash scatter mpg weight, legend(order(1 2)) name(g27)
di "RESULT|027|rc=" _rc
dash clear
capture dash scatter mpg weight, ti("abbrev ti") name(g28)
di "RESULT|028|rc=" _rc
dash clear
capture dash scatter mpg weight, mlab(make) name(g29)
di "RESULT|029|rc=" _rc
dash clear
capture dash scatter mpg weight, msym(O) name(g30)
di "RESULT|030|rc=" _rc
dash clear
capture dash scatter mpg weight, xlab(2000(500)4000) name(g31)
di "RESULT|031|rc=" _rc
dash clear
capture dash scatter mpg weight, mcol(navy) name(g32)
di "RESULT|032|rc=" _rc
dash clear
capture dash scatter mpg weight, lcol(navy) name(g33)
di "RESULT|033|rc=" _rc
dash clear
capture dash scatter mpg weight, scheme(economist) name(g34)
di "RESULT|034|rc=" _rc
dash clear
capture dash tsline mpg, name(g35)
di "RESULT|035|rc=" _rc
dash clear
capture dash contour mpg weight price, name(g36)
di "RESULT|036|rc=" _rc
dash clear
capture dash pccapsym mpg weight price t, name(g37)
di "RESULT|037|rc=" _rc
dash clear
capture dash scatter mpg weight, level(90) name(g38)
di "RESULT|038|rc=" _rc
dash clear
capture dash scatter mpg weight, ylabel(, format(%9.0fc)) name(g39)
di "RESULT|039|rc=" _rc
dash clear
capture dash scatter mpg weight, xlabel(#10) name(g40)
di "RESULT|040|rc=" _rc
dash clear
capture dash scatter mpg weight, xlabel(minmax) name(g41)
di "RESULT|041|rc=" _rc
dash clear
capture dash scatter mpg weight, yscale(range(0 50)) name(g42)
di "RESULT|042|rc=" _rc
dash clear
capture dash scatter mpg weight, graphregion(margin(zero)) name(g43)
di "RESULT|043|rc=" _rc
dash clear
capture dash scatter mpg weight, t1title(top) name(g44)
di "RESULT|044|rc=" _rc
dash clear
capture dash scatter mpg weight, b1title(bot) name(g45)
di "RESULT|045|rc=" _rc
dash clear
capture dash scatter mpg weight, title2(second) name(g46)
di "RESULT|046|rc=" _rc
dash clear
capture dash area mpg weight, color(navy) name(g47)
di "RESULT|047|rc=" _rc
dash clear
capture dash bar mpg weight, color(navy) name(g48)
di "RESULT|048|rc=" _rc
dash clear
capture dash scatter mpg weight, blabel(total) name(g49)
di "RESULT|049|rc=" _rc
dash clear
capture dash scatter mpg weight, name(g50)
di "RESULT|050|rc=" _rc
dash clear
capture dash scatter mpg weight, mc(navy) ms(O) msi(small) name(g51)
di "RESULT|051|rc=" _rc
dash clear
capture dash scatter mpg weight, xla(2000 3000 4000) name(g52)
di "RESULT|052|rc=" _rc
dash clear
capture dash scatter mpg weight, xlabel(2000 3000 4000) name(g53)
di "RESULT|053|rc=" _rc
dash clear
capture dash scatter mpg weight, ti(T) name(g54)
di "RESULT|054|rc=" _rc
dash clear
capture dash histogram mpg, name(g55)
di "RESULT|055|rc=" _rc
dash clear
capture dash kdensity mpg, name(g56)
di "RESULT|056|rc=" _rc
dash clear
capture dash lfitci mpg weight, name(g57)
di "RESULT|057|rc=" _rc
dash clear
capture dash lowess mpg weight, name(g58)
di "RESULT|058|rc=" _rc
