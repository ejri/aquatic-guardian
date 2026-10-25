"""Command line: ``python -m plumes2py <command>``.

  example                       run the PLUMES2.0 Example_project
  run FOLDER [--flow-units MGD] run PLUMES2.0 CSV inputs saved by the GUI
  scenario FILE.json            run a JSON scenario (as written by --dump)
  datacentre --it-mw 24 ...     build and run a data-centre cooling scenario
Add --json to print the full result as JSON, --rule wa_marine|ca_new_coastal|...
to screen against a rule, --critical / --tidal U / --mc N for multi-run analyses.
"""
from __future__ import annotations

import argparse
import json
import sys

from .datacenter import DataCentreDesign, build
from .inputs import Scenario, load_plumes2_csvs, reference_example
from .model import run
from .report import text_report
from .scenarios import critical_conditions, monte_carlo, tidal_cycle, tornado


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="plumes2py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["example", "run", "scenario", "datacentre"])
    p.add_argument("path", nargs="?")
    p.add_argument("--flow-units", default="MGD")
    p.add_argument("--json", action="store_true")
    p.add_argument("--dump", help="write the scenario as JSON to this file")
    p.add_argument("--rule", default=None)
    p.add_argument("--wa-category", default="excellent")
    p.add_argument("--increment", type=float, default=None)
    p.add_argument("--critical", action="store_true")
    p.add_argument("--tidal", type=float, default=None, help="peak tidal current, m/s")
    p.add_argument("--mc", type=int, default=0)
    p.add_argument("--tornado", action="store_true")
    for k, v in DataCentreDesign().__dict__.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            p.add_argument("--" + k.replace("_", "-"), type=type(v), default=None)
    p.add_argument("--mode", default=None)
    p.add_argument("--sst", type=float, default=12.0)
    p.add_argument("--salinity", type=float, default=31.0)
    p.add_argument("--current", type=float, default=0.1)
    p.add_argument("--acute", type=float, default=30.0)
    p.add_argument("--chronic", type=float, default=300.0)
    a = p.parse_args(argv)

    if a.command == "example":
        sc = reference_example()
    elif a.command == "run":
        sc = load_plumes2_csvs(a.path, flow_units=a.flow_units)
    elif a.command == "scenario":
        sc = Scenario.from_dict(json.load(open(a.path)))
    else:
        d = DataCentreDesign()
        for k in d.__dict__:
            v = getattr(a, k, None)
            if v is not None:
                setattr(d, k, v)
        sc = build(d, sst_c=a.sst, salinity=a.salinity, current_ms=a.current,
                   acute_m=a.acute, chronic_m=a.chronic)
    if a.dump:
        json.dump(sc.to_dict(), open(a.dump, "w"), indent=2)
    res = run(sc, rule=a.rule, wa_category=a.wa_category, custom_increment=a.increment,
              convergence_check=True)
    extra = {}
    if a.critical:
        extra["critical"] = critical_conditions(sc, rule=a.rule)
    if a.tidal:
        extra["tidal"] = tidal_cycle(sc, a.tidal, rule=a.rule)
    if a.mc:
        extra["monte_carlo"] = monte_carlo(sc, n=a.mc)
    if a.tornado:
        extra["tornado"] = tornado(sc)
    if a.json:
        res.update(extra)
        json.dump(res, sys.stdout, indent=1, default=float)
        print()
    else:
        print(text_report(res, sc.settings.nearfield_output_interval))
        for k, v in extra.items():
            print(f"\n== {k} ==")
            print(json.dumps(v, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
