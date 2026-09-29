# Aquatic Disclosure metrics (schema version 0.1.0)

| Field | Unit | Definition |
|---|---|---|
| `thermal.heat_rejected_mwh` | MWh | Total heat rejected by the facility in the period; equal to total facility electricity consumption |
| `thermal.heat_to_water_mwh` | MWh | Heat discharged to surface water or seawater, after heat recovered before discharge |
| `thermal.heat_reused_mwh` | MWh | Heat recovered from the cooling system and delivered to a beneficial use before any discharge |
| `thermal.erf` | fraction | Energy reuse factor, ISO/IEC 30134-6 |
| `thermal.discharge_delta_t_k` | K | Discharge temperature minus intake (or ambient) temperature: mean, 95th percentile and maximum of hourly values |
| `thermal.mixing_zone.*` | various | Criterion used, its legal basis, radius, hours of exceedance at the edge, and the model used |
| `thermal.cold_shock_events` | count | Shutdowns with a temperature drop at the outfall faster than the permit ramp rate |
| `intake.design_intake_m3s` | m³/s | Maximum design withdrawal capacity |
| `intake.cooling_fraction` | fraction | Share of withdrawn water used for cooling (the §316(b) 25 % test) |
| `intake.through_screen_velocity_ms` | m/s | Maximum design through-screen velocity |
| `biology.impingement[]`, `biology.entrainment[]` | count | Organisms by taxon, species where known, life stage, sentience tier and method |
| `chemicals[]` | kg | Mass of active ingredient by substance and purpose |
| `noise.*` | dB re 1 µPa at 1 m, Hz | Source level and frequency band |
| `emf.*` | kV, m, µT | Cable voltage, AC or DC, burial depth, field at 1 m |
| `freshwater.*` | m³, L/kWh | Withdrawal, consumption and WUE (ISO/IEC 30134-9) |
| `heat_reuse.aquaculture.*` | various | Species, named welfare standard, stocking density, mortality, stunning method |
| `provenance.*` | text | Who prepared the record, how, with which tool versions; whether independently verified; whether design-value screening |
