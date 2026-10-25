"""Write browser-parity fixtures: scenario inputs plus the Python results the
JavaScript engine (site/js/plumes2.js) must reproduce. Run from python/:
    python scripts/make_parity_fixtures.py ../tests/fixtures/parity.json
"""
import copy, json, sys
from plumes2py import (Ambient, AmbientRow, Diffuser, Effluent, MixingZone, Scenario, Settings,
                       reference_example, run)
from plumes2py.datacenter import DataCentreDesign, build

def strat(speed=0.1, direction=0.0):
    return Ambient([AmbientRow(depth=z, speed=speed * (1 - z / 60), direction=direction + z, salinity=30 + z / 10,
                               temperature=16 - z / 3, far_speed=speed, far_direction=direction, alpha=0.0003)
                    for z in (0, 5, 10, 20, 30)])

def cases():
    out = []
    ex = reference_example(); out.append(("epa_example", ex, {}))
    t = reference_example(); t.settings.max_rise_fall = 0; out.append(("epa_stop_at_trap", t, {}))
    for case in ("constant", "linear"):
        c = reference_example(); c.settings.farfield_case = case; out.append((f"epa_farfield_{case}", c, {}))
    out.append(("dc_24mw_outfall", build(DataCentreDesign(), sst_c=12, salinity=31, current_ms=0.15), {"rule": "wa_marine"}))
    out.append(("dc_pod", build(DataCentreDesign(it_mw=2.3, mode="pod", n_ports=1, port_depth=10), sst_c=18,
                                salinity=30, current_ms=0.2), {"rule": "ca_new_coastal"}))
    out.append(("single_port_stratified", Scenario(Diffuser(0.4, 1.0, 30, 15, port_depth=25),
               Effluent(0.5, salinity=31, temperature=24, concentration=50), strat(0.12, 45),
               MixingZone(20, 200), Settings()), {"rule": "or_marine"}))
    brine = Scenario(Diffuser(0.15, 1.5, 60, 0, n_ports=3, spacing=5, port_depth=20),
                     Effluent(0.05, salinity=65, temperature=14), strat(0.08), MixingZone(10, 100), Settings())
    out.append(("brine_sinking", brine, {}))
    slack = build(DataCentreDesign(it_mw=50, n_ports=8, spacing=6), sst_c=15, salinity=32, current_ms=0.01)
    out.append(("slack_water", slack, {"rule": "custom", "custom_increment": 1.0}))
    return out

def pick(res):
    m = res["metrics"]
    ff = res["farfield"]
    return {
        "end": res["nearfield"]["end"], "termination": res["nearfield"]["termination"],
        "n_steps": len(res["nearfield"]["steps"]), "events": [(e["event"], e["step"]) for e in res["nearfield"]["events"]],
        "step10": res["nearfield"]["steps"][min(10, len(res["nearfield"]["steps"]) - 1)],
        "farfield_rows": None if not ff else [ff["rows"][0], ff["rows"][len(ff["rows"]) // 2], ff["rows"][-1]],
        "w0": None if not ff else ff["w0"],
        "thermal": {k: v for k, v in m["thermal"].items() if k != "threshold_reach"},
        "reach": m["thermal"]["threshold_reach"], "exposure": m["exposure"], "oxygen": m["oxygen"],
        "heat": m["heat"], "flow_class": {k: v for k, v in m["flow_class"].items() if k != "note"},
        "merging": m.get("merging"), "caveats": res["caveats"],
        "verdict": res.get("compliance", {}).get("verdict"),
    }

if __name__ == "__main__":
    fx = []
    for name, sc, opt in cases():
        res = run(sc, **opt)
        fx.append({"name": name, "scenario": sc.to_dict(), "options": opt, "expect": pick(res)})
    json.dump(fx, open(sys.argv[1], "w"), indent=1, default=float)
    print(f"wrote {len(fx)} fixtures")
