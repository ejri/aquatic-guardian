"""The browser engine (app/engine.js) must reproduce the Python reference exactly."""
import json, math, random, shutil, subprocess
from pathlib import Path
import pytest
from aquatic_guardian import criteria, screening

ROOT = Path(__file__).resolve().parents[1]
JURISDICTION_IDS = sorted(criteria.load_jurisdictions())
NUMERIC = [("heat_rejected_mw",), ("heat_to_water_mw",), ("flow_m3s",), ("tidal_excursion_m",),
           ("intake_316b", "design_intake_mgd"), ("intake_316b", "min_screen_open_area_m2"),
           ("tidal_volume_check", "fraction"), ("temperature_rule", "allowed_increment_k"),
           ("near_field", "dilution"), ("near_field", "delta_t_near_field_k"), ("near_field", "g_prime"),
           ("water_quality", "do_sat_ambient_mg_l"), ("water_quality", "do_sat_discharge_mg_l"),
           ("water_quality", "nh3_frac_ambient"), ("water_quality", "nh3_frac_ratio"),
           ("numerics", "k_num_upwind_m2s"), ("numerics", "crossover_scale_m")]


def scenarios(n=200, seed=3):
    """Randomised facilities. Every jurisdiction id appears at least ceil(n/len) times,
    so the parity check covers each jurisdiction's rule and intake mapping."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        out.append({
            "jurisdiction": JURISDICTION_IDS[i % len(JURISDICTION_IDS)],
            "it_load_mw": rng.uniform(1, 300), "pue": rng.uniform(1.02, 1.6),
            "cooling_type": rng.choice(["once_through", "hybrid", "closed_loop_air"]),
            "reuse_fraction": rng.choice([0.0, 0.1, 0.3]), "delta_t_k": rng.uniform(2, 15),
            "water_type": rng.choice(["marine", "estuarine", "fresh"]),
            "t_ambient_c": rng.uniform(4, 24), "s_psu": rng.uniform(5, 35), "ph": rng.uniform(6.8, 8.4),
            "u_peak_ms": rng.uniform(0.02, 1.2), "depth_m": rng.uniform(4, 80),
            "n_ports": rng.randint(1, 40), "port_diameter_m": rng.uniform(0.1, 1.0),
            "port_spacing_m": rng.uniform(1, 60),
            # None means "use the jurisdiction's rule"; the others override it.
            "temperature_rule": rng.choice([None, "wa_marine", "ca_new_coastal", "custom"]),
            "wa_category": rng.choice(["extraordinary", "excellent", "good", "fair"]),
            "custom_increment_k": rng.uniform(0.3, 3), "grid_dx_m": rng.uniform(5, 200),
            "grid_dt_s": rng.uniform(1, 20), "aquaculture_reuse": rng.random() < 0.3})
    return out


def get(d, path):
    for p in path:
        if d is None:
            return None
        d = d[p]
    return d


def _node(expr: str):
    js = (f"const E=require({json.dumps(str(ROOT / 'app' / 'engine.js'))});"
          f"process.stdout.write(JSON.stringify({expr}));")
    return json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True,
                                     check=True).stdout)


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_jurisdiction_tables_match_criteria_json():
    """app/engine.js carries a copy of the jurisdictions section of data/criteria.json.
    The copy must be exact, including notes and citations."""
    data = json.loads((ROOT / "data" / "criteria.json").read_text())
    assert _node("E.INTAKE_RULES") == data["intake_rules"]
    js = _node("E.JURISDICTIONS")
    assert [j["id"] for j in js] == [j["id"] for j in data["jurisdictions"]]
    for a, b in zip(js, data["jurisdictions"]):
        assert a == b, a["id"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("jid", JURISDICTION_IDS)
def test_js_jurisdiction_lookup_matches_python(jid):
    assert _node(f"E.jurisdiction({json.dumps(jid)})") == criteria.jurisdiction(jid)


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_engine_matches_python(tmp_path):
    sc = scenarios()
    assert {s["jurisdiction"] for s in sc} == set(JURISDICTION_IDS)
    (tmp_path / "in.json").write_text(json.dumps(sc))
    js = (f"const E=require({json.dumps(str(ROOT / 'app' / 'engine.js'))});"
          f"const fs=require('fs');const s=JSON.parse(fs.readFileSync({json.dumps(str(tmp_path / 'in.json'))}));"
          "process.stdout.write(JSON.stringify(s.map(x=>E.screen(x))));")
    res = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
    for inp, js_out in zip(sc, res):
        py = screening.screen(inp)
        for path in NUMERIC:
            a, b = get(py, path), get(js_out, path)
            if a is None or b is None:
                assert a is None and b is None, path
                continue
            if isinstance(a, float) and (math.isnan(a) or math.isinf(a)):
                continue
            assert b == pytest.approx(a, rel=1e-9, abs=1e-12), (path, inp)
        assert [f["id"] for f in py["flags"]] == [f["id"] for f in js_out["flags"]], inp
        assert [f["text"] for f in py["flags"]] == [f["text"] for f in js_out["flags"]], inp
        assert py["jurisdiction"] == js_out["jurisdiction"], inp
        assert py["temperature_rule"]["basis"] == js_out["temperature_rule"]["basis"], inp
        if py["near_field"]:
            assert py["near_field"]["regime"] == js_out["near_field"]["regime"]
            assert py["near_field"]["meets_rule"] == js_out["near_field"]["meets_rule"]
