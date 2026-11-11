"""dash_render._dash_fast_defaults: Bokeh's defaults worked out once per
(property, model class), and still Bokeh's defaults (11nov2026).

The renderer patches Bokeh's PropertyDescriptor so an unset property's
default -- when it is stable and immutable and no theme overrides it -- is
computed once per model class rather than on every read.  These tests hold
the patched answers to Bokeh's own (kept as ``_dash_real_defaults``) for
every property of every Bokeh model, and check the cases the cache must not
touch: a theme, a set value, a mutable or unstable default.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dash_render as dr  # noqa: E402
from bokeh.core.has_props import HasProps  # noqa: E402
from bokeh.core.property.descriptors import PropertyDescriptor  # noqa: E402
from bokeh.model import Model  # noqa: E402
import bokeh.models  # noqa: E402,F401  (registers every model class)


def _model_classes():
    out = []
    for cls in Model.model_class_reverse_map.values():
        if cls.__module__.startswith("bokeh."):
            out.append(cls)
    return sorted(out, key=lambda c: (c.__module__, c.__qualname__))


def _same(a, b):
    """Equal, as a default is: NaN equals NaN, and the types match."""
    if type(a) is not type(b):
        return False
    if isinstance(a, float) and a != a:
        return b != b
    if isinstance(a, tuple):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    return a == b


def _fresh(cls):
    try:
        return cls()
    except Exception:
        return None


class TestThePatchIsOn:
    def test_the_descriptor_is_patched_once(self):
        assert PropertyDescriptor._dash_fast_defaults is True
        real = PropertyDescriptor._dash_real_defaults
        assert dr._dash_fast_defaults() is True
        # A second call (dash_render.py runs again on every dash call)
        # leaves the first patch, wrapping nothing twice.
        assert PropertyDescriptor._dash_real_defaults is real
        assert PropertyDescriptor._get_default is not real[0]
        assert PropertyDescriptor.has_unstable_default is not real[1]

    def test_a_bokeh_without_the_methods_is_left_alone(self, monkeypatch):
        class _Bare:
            pass

        fake = type(sys)("bokeh.core.property.descriptors")
        fake.PropertyDescriptor = _Bare
        monkeypatch.setitem(sys.modules, "bokeh.core.property.descriptors",
                            fake)
        assert dr._dash_fast_defaults() is False
        assert not hasattr(_Bare, "_get_default")
        assert not hasattr(_Bare, "_dash_fast_defaults")

    def test_a_bokeh_that_cannot_be_imported_is_left_alone(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "bokeh.core.property.descriptors",
                            None)
        assert dr._dash_fast_defaults() is False


class TestEveryDefaultIsBokehs:
    def test_every_property_of_every_model(self):
        real_default, real_unstable = PropertyDescriptor._dash_real_defaults
        checked = 0
        for cls in _model_classes():
            a, b = _fresh(cls), _fresh(cls)
            if a is None:
                continue
            for name in sorted(cls.properties(_with_props=True)):
                desc = cls.lookup(name)
                if not isinstance(desc, PropertyDescriptor) \
                        or name in a._property_values:
                    continue
                assert desc.has_unstable_default(a) == \
                    bool(real_unstable(desc, b)), (cls, name)
                got = desc._get_default(a)
                # A second read: the cached answer when there is one.
                again = desc._get_default(a)
                want = real_default(desc, b)
                if desc.has_unstable_default(a):
                    assert again is got, (cls, name)
                    assert type(got) is type(want), (cls, name)
                else:
                    assert _same(got, want), (cls, name, got, want)
                    assert _same(again, want), (cls, name)
                checked += 1
        assert checked > 5000

    def test_the_models_serialise_as_before(self):
        real_default, real_unstable = PropertyDescriptor._dash_real_defaults
        for cls in _model_classes():
            a = _fresh(cls)
            if a is None:
                continue
            fast = a.properties_with_values(include_defaults=True,
                                              include_undefined=True)
            saved = (PropertyDescriptor._get_default,
                     PropertyDescriptor.has_unstable_default)
            try:
                PropertyDescriptor._get_default = real_default
                PropertyDescriptor.has_unstable_default = real_unstable
                b = _fresh(cls)
                slow = b.properties_with_values(include_defaults=True,
                                                  include_undefined=True)
            finally:
                (PropertyDescriptor._get_default,
                 PropertyDescriptor.has_unstable_default) = saved
            assert sorted(fast) == sorted(slow), cls
            for k in fast:
                if isinstance(fast[k], HasProps):
                    assert type(fast[k]) is type(slow[k]), (cls, k)
                elif isinstance(fast[k], (list, dict, set)):
                    assert type(fast[k]) is type(slow[k]), (cls, k)
                    assert len(fast[k]) == len(slow[k]), (cls, k)
                else:
                    assert _same(fast[k], slow[k]), (cls, k)


class TestWhatTheCacheLeavesToBokeh:
    def test_a_theme_still_overrides_the_default(self):
        from bokeh.models import Title
        t = Title()
        assert t.text_font_size == Title().text_font_size
        t.apply_theme({"text_font_size": "31px"})
        assert t.text_font_size == "31px"
        assert Title().text_font_size != "31px"
        t.unapply_theme()
        assert t.text_font_size == Title().text_font_size

    def test_a_set_value_wins(self):
        from bokeh.models import Title
        t = Title()
        _ = t.text_font_size
        t.text_font_size = "9px"
        assert t.text_font_size == "9px"
        assert Title().text_font_size != "9px"

    def test_a_mutable_default_is_never_shared(self):
        from bokeh.models import Plot
        a, b = Plot(), Plot()
        a.renderers.append(bokeh.models.GlyphRenderer())
        assert len(b.renderers) == 0
        assert len(Plot().renderers) == 0

    def test_a_subclass_override_is_its_own(self):
        # figure() overrides Plot's defaults; each class keeps its own.
        from bokeh.models import Plot
        from bokeh.plotting import figure
        real_default = PropertyDescriptor._dash_real_defaults[0]
        for name in ("width", "height", "toolbar_location", "min_border",
                     "output_backend"):
            d = Plot.lookup(name)
            f, p = figure(), Plot()
            if name not in f._property_values:
                assert getattr(f, name) == real_default(d, figure()), name
            assert getattr(p, name) == real_default(d, Plot()), name
        assert Plot.lookup("toolbar_location")._get_default(Plot()) \
            == real_default(Plot.lookup("toolbar_location"), Plot())


class TestTheServedAppCarriesIt:
    def test_the_app_copies_the_function_and_calls_it(self, tmp_path):
        import inspect
        import json
        import subprocess
        import textwrap
        import numpy as np
        import pandas as pd
        from conftest import make_data_json, make_spec
        df = pd.DataFrame({"mpg": np.linspace(12.0, 41.0, 12),
                           "weight": np.linspace(1760.0, 4840.0, 12)})
        spec = make_spec([{"type": "scatter", "yvar": "mpg",
                           "xvar": "weight", "options": {}}])
        sp, dp = tmp_path / "spec.json", tmp_path / "data.json"
        ap = tmp_path / "app.py"
        sp.write_text(json.dumps(spec))
        dp.write_text(json.dumps(make_data_json(df)))
        dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
        src = ap.read_text(encoding="utf-8")
        body = textwrap.dedent(inspect.getsource(dr._dash_fast_defaults))
        assert body.strip() in src
        call = "\n_dash_fast_defaults()\n"
        assert call in src
        # After the bokeh imports, so the descriptor it patches is loaded.
        assert src.index("_dash_dep_fail('bokeh', _dash_e)") < src.index(call)
        # The app's own process, with no dash_render, is patched by it.
        probe = (
            "import importlib.util, sys\n"
            "s = importlib.util.spec_from_file_location('dash_app', sys.argv[1])\n"
            "m = importlib.util.module_from_spec(s); s.loader.exec_module(m)\n"
            "from bokeh.core.property.descriptors import PropertyDescriptor as P\n"
            "assert 'dash_render' not in sys.modules\n"
            "print(P._dash_fast_defaults, len(m.curdoc().roots) > 0)\n")
        proc = subprocess.run([sys.executable, "-c", probe, str(ap)],
                              capture_output=True, text=True, timeout=120,
                              cwd=str(tmp_path))
        assert proc.returncode == 0, proc.stderr[-2000:]
        assert proc.stdout.split() == ["True", "True"], proc.stdout
