"""UM3 rebuild against the PLUMES2.0 Example_project reference output
(ModelResults_TxtOutputs.dat, github.com/ssmc-uw/PLUMES2.0)."""
import math
import pytest
from plumes2py import reference_example, run_nearfield

REF_STEPS = {5: (1.101, 0.083, 0.011, 0.007, -10.987), 10: (1.213, 0.091, 0.024, 0.014, -10.972),
             15: (1.337, 0.101, 0.038, 0.022, -10.956), 25: (1.624, 0.122, 0.071, 0.040, -10.919)}
# (depth, dilution, x) along the trajectory, compared at equal depth
REF_PATH = [(-10.789, 2.650, 0.185), (-10.259, 7.092, 0.663), (-9.024, 19.049, 1.758),
            (-7.536, 38.072, 2.963), (-6.726, 51.232, 3.583), (-5.132, 84.036, 4.785),
            (-4.024, 113.094, 5.639), (-3.263, 137.648, 6.256)]
REF_END = dict(dilution=169.754, diameter=6.481, x=7.017, y=2.082, depth=2.512)

@pytest.fixture(scope="module")
def res():
    return run_nearfield(reference_example())

def at_depth(r, z):
    for a, b in zip(r.steps, r.steps[1:]):
        if (a.depth + z) * (b.depth + z) <= 0 and a.depth != b.depth:
            f = (a.depth + z) / (a.depth - b.depth)
            return a.dilution + f * (b.dilution - a.dilution), a.x + f * (b.x - a.x)

@pytest.mark.parametrize("step", sorted(REF_STEPS))
def test_jet_phase_step_by_step(res, step):
    dil, dia, x, y, z = REF_STEPS[step]
    s = res.steps[step]
    assert s.dilution == pytest.approx(dil, abs=0.002)   # 2.00 % mass growth per step
    assert s.diameter == pytest.approx(dia, abs=0.002)
    assert s.x == pytest.approx(x, abs=0.002) and s.y == pytest.approx(y, abs=0.002)
    assert -s.depth == pytest.approx(z, abs=0.002)

def test_trajectory_rms_dilution_error_under_4pct(res):
    errs = [math.log(at_depth(res, z)[0] / d) for z, d, _ in REF_PATH]
    rms = math.sqrt(sum(e * e for e in errs) / len(errs))
    assert rms < 0.04, errs
    assert max(abs(e) for e in errs) < 0.065

def test_trajectory_position(res):
    for z, _, x in REF_PATH:
        assert at_depth(res, z)[1] == pytest.approx(x, abs=0.08)

@pytest.mark.parametrize("key,tol", [("dilution", 0.012), ("diameter", 0.015), ("x", 0.01),
                                     ("y", 0.01), ("depth", 0.01)])
def test_terminal_state_within_tolerance(res, key, tol):
    assert getattr(res.end, key) == pytest.approx(REF_END[key], rel=tol)

def test_event_sequence(res):
    names = [e["event"] for e in res.events]
    assert names.index("trap") < names.index("merging") < names.index("surface")
    assert res.termination == "surface"
