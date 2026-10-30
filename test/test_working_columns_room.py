"""The working columns are counted against c(maxvar) first (WP-31 G3d).

GAPS3 G3: dash generates its qualifier, join-order, time-series and weight
columns in the user's data, and at c(maxvar) generate stopped partway with
Stata's "no room to add more variables", r(900).  _dash_maxvar_room counts
them on both routes before the first is made (test_qualifier_in_stata.cscript
U55-7 runs it at maxvar 2048).
"""
import os
import re

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def _ado():
    with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
        return [l.split("//", 1)[0] for l in fh.read().splitlines()]


class TestTheRoomIsCountedFirst:
    def test_both_routes_count_before_any_generator(self):
        lines = _ado()
        checks = [i for i, l in enumerate(lines)
                  if re.match(r"\s*(capture noisily )?_dash_maxvar_room "
                              r"`_dq_n'", l)]
        gens = [i for i, l in enumerate(lines)
                if re.match(r"\s*(capture noisily )?(`_xfp' )?"
                            r"_dash_(qual|sort|tsop|wexp)_gen \"", l)]
        # 2 -> 3 checks, 8 -> 12 generators: WP-33 33-07's multi-frame
        # path (_dash_frames_one) makes the columns in each frame, after its
        # own count.  Flipped (WP-35 DT-19): 33-07's four generators moved
        # into _dash_frames_part, which _dash_frames_one runs after its
        # count (in place or in a temporary frame), and each route's
        # generators run after its count, in place or prefixed `_xfp'; the
        # gap grew by the frame branch's lines (12 -> 45).
        assert len(checks) == 3 and len(gens) == 12
        for c in checks:
            after = [g for g in gens if g > c]
            nearest = after[:4]
            assert len(nearest) == 4 and nearest[0] - c < 45, c + 1
        for c in checks:
            args = lines[c].replace("capture noisily ", "").split()
            # Flipped (WP-40 plat:PT-7): the two routes count the selection
            # column beside the weight columns, `=`_dwx_n' + `_sel_mode''
            # (it exists with every other working column at the export);
            # 33-07's per-frame count is unchanged.
            assert args[1:4] == ["`_dq_n'", "`_ds_n'", "`_dts_n'"]
            assert args[4] in ("`_dwx_n'", "`=`_dwx_n'+`_sel_mode''"), args[4]
            # WP-35 DT-19: the count of the variables the export reads.
            assert args[6] == "`_mv_kx'", c + 1

    def test_the_refusal_is_r900_in_dashs_words(self):
        lines = _ado()
        start = next(i for i, l in enumerate(lines)
                     if l.startswith("program define _dash_maxvar_room"))
        end = next(i for i in range(start, len(lines)) if lines[i] == "end")
        body = "\n".join(lines[start:end])
        assert "c(maxvar) - c(k)" in body
        assert "exit 900" in body
        assert "the dashboard needs" in body
