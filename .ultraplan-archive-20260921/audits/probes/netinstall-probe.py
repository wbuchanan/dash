import importlib.util, json, os, sys, traceback
SP = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.join(SP, "netinst2")
spec = {"build_options": {"theme": "default", "layout": "auto", "title": "T",
                          "subtitle": "", "link": "", "filter": "",
                          "filter_position": "top"},
        "graphs": [{"name": "g1", "plots": [{"type": "scatter", "yvar": "y", "xvar": "x",
                     "options": {}}], "graph_options": {}}],
        "kpis": []}
data = {"data": {"values": [{"x": 1.0, "y": 2.0}, {"x": 2.0, "y": 3.0}, {"x": 3.0, "y": 5.0}],
                 "variableLabels": {}, "valueLabels": {}, "valueLabelNames": {},
                 "variableTypeIsString": {"x": False, "y": False}}}
sp_p = os.path.join(SP, "ni_spec.json"); dt_p = os.path.join(SP, "ni_data.json")
json.dump(spec, open(sp_p, "w")); json.dump(data, open(dt_p, "w"))

for label, root in (("WITH schemes/ (dev tree)", "/Users/billy/Desktop/Programs/StataPrograms/d/dash"),
                    ("WITHOUT schemes/ (net install)", HOME)):
    print("=== %s ===" % label)
    s = importlib.util.spec_from_file_location("dr_%s" % abs(hash(root)),
                                               os.path.join(root, "dash_render.py"))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    try:
        r = m.DashRenderer(sp_p, dt_p)
        print("   DashRenderer constructed OK; scheme =", getattr(r.scheme, "name", "?"))
    except Exception as e:
        print("   RAISED:", type(e).__name__, str(e)[:180])
