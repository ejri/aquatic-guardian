"""Current and tide tiles must read different marine fields (audit P1)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "site" / "js" / "ocean-data.js").read_text()
OBS = (ROOT / "site" / "js" / "observatory.js").read_text()


def test_ocean_data_exposes_distinct_current_and_tide_fields():
    assert "current_ms:" in JS
    assert "tide_range_m:" in JS
    # tide_range comes from sea_level span; current from ocean_current_velocity
    assert "ocean_current_velocity" in JS
    assert "sea_level_height_msl" in JS


def test_observatory_tiles_bind_distinct_data_fields():
    assert 'data-field="current_ms"' in OBS
    assert 'data-field="tide_range_m"' in OBS
    assert "tide_range_m" in OBS and "current_ms" in OBS


def test_temperature_tiles_prefer_crw():
    # Prefer reef (CRW) SST over Open-Meteo when both exist
    assert "r.sst_c != null ? fmt(r.sst_c" in OBS or "r.sst_c != null" in OBS
    assert "CRW" in OBS


def test_conditions_charts_and_maplibre():
    assert "obs-sst-svg" in OBS and "obs-dhw-svg" in OBS
    assert "MMM+1" in OBS
    assert "DHW 4" in OBS and "DHW 8" in OBS
    assert "maplibregl" in OBS or "maplibre" in OBS.lower()
    assert "coralReefWatchSeries" in JS
    assert "openMeteoSst90" in JS
    assert "past_days=90" in JS or "pastDays" in JS
