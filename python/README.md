# plumes2py

Python rebuild of EPA PLUMES 2.0 (UM3 near field, Brooks far field) with thermal, biological and regulatory
screening metrics. Reproduces the EPA reference run to 1.2 % at the surfacing point; see `../VALIDATION.md`.

```bash
pip install -e .
python -m plumes2py example --rule wa_marine          # EPA Example_project, PLUMES-format output
python -m plumes2py run path/to/plumes2_project/      # re-run CSVs saved by the PLUMES 2.0 GUI
python -m plumes2py datacentre --it-mw 24 --sst 12 --salinity 31 --current 0.15 --rule wa_marine --tidal 0.4
python -m pytest -q
```

```python
from plumes2py import reference_example, run
res = run(reference_example(), rule="wa_marine", convergence_check=True)
res["metrics"]["nearfield"]["dilution"], res["metrics"]["thermal"]["dt_chronic_c"]
```
