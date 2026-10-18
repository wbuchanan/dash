*! serve_dashboard.do
*! Example: a dashboard written as a Bokeh Server app, the form a filter
*! recomputes on the server.
*!
*! WHY THIS EXISTS
*!   No example showed server mode.  `dash serve' runs in the foreground
*!   until you press Break, so this file writes the app with
*!   `dash build, server' instead (which runs to the end, as an example
*!   must under certification) and shows the serve line in a comment.
*!
*! Usage:  do examples/serve_dashboard.do
*!         (run from the dash/ directory)
*!
*! Produces: serve_dashboard_app.py
*! Version: 0.1.0  18oct2026

sysuse auto, clear
dash clear

dash (scatter mpg weight) (lfit mpg weight),   ///
    title("Mileage and weight")                    ///
    name(fit)

dash histogram price, title("Price") name(hist)

dash kpi mean(price), title("Mean price") fmt(%9.0fc) name(k1)

// server writes a Bokeh Server .py app instead of a standalone page;
// it does not start the server.
dash build,                                         ///
    saving("serve_dashboard_app.py") server replace ///
    title("dash server mode")                       ///
    filter(foreign, type(dropdown) label("Origin"))

// To serve it: dash serve, port(5006)
//   run in this session after this file: dash serve launches a Bokeh
//   Server on the registry above, and Stata waits until you press Break
//   or timeout() expires.
// or: python serve_dashboard_app.py
//   the "To launch:" line dash build, server printed above; the app
//   prints the path of a file holding the link that opens the dashboard.

display as text "serve_dashboard.do: wrote serve_dashboard_app.py"
