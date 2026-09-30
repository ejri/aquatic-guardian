# Changelog

## 0.2.1 (2026-09-29)
- Correction 7: merged plumes can no longer out-dilute isolated ones; the default design's screening rise rises from 0.32 °C to 0.46 °C (library, browser engine, Lab, results regenerated).
- Lab: new "near versus far" panel showing the near-field peak and far-field layer average side by side, live, with why they differ.
- Lab camera geometry: flat-port refraction option; the "before fix" preset is now labelled as reconstructed, with its assumed specs stated.
- Camera geometry moved into the library (`tracking.fov_width`, `tracking.camera_screen`) and mirrored in `app/sims.js`.
- Permanent tests for the browser 2-D solver's flux-limited scheme (both tide directions, heat conservation, source bookkeeping).
- `benchmarks/plumes2/`: case matrix, run guide, results template and comparison script for benchmarking against EPA PLUMES 2.0 (UM3). default suite green (`pytest -q -m "not slow and not site"`).

## 0.2.0 (2026-09-29)
- Website rebuilt as audience-specific sections: public (follow-the-water walkthrough, sentience tiers, letters to representatives, EU consultation countdown), officials (jurisdiction toolkit, timeline of instruments, screening with draft permit conditions, recommendations), researchers (the Lab) and industry (design comparison, temperature-rise trade-off, disclosure record, heat reuse).
- The Lab shows results from all three notebooks, recomputed with fixed seeds by `app/notebook_results.py`, plus nine live simulations: tidal plume (TVD versus upwind), near field with the per-port bug, numerical diffusion, safety margin, turbidity confound, underwater imaging, camera geometry, school tracking with a Kalman filter, and yield versus loop temperature.
- New library functions: `tracking.simulate_school`, `tracking.kalman_cv`, signed-current transport in `numerics.advect_diffuse_1d`.
- New browser kernels in `app/sims.js`, parity-tested against the Python library; 51 checks in total.

## 0.1.0 (2026-09-29)
- Framework v0.1 (public consultation draft): five layers, three coverage tiers, sentience tiers.
- Model language for US federal and state, permits, EU, Canada, BBNJ, ISO/IEC and the UK.
- Python library with verified screening physics, water quality, occupancy, imaging, tracking and bioenergetics modules; 40 tests.
- Six technical corrections from the September 2026 fact-check (docs/CORRECTIONS.md).
- Aquatic Disclosure Schema 0.1.0 and notebook handoff schema 0.1.0.
- Browser screening engine with parity tests; public website and screening app.
- AGENTS.md, Cursor project rules and a phased Cursor prompt pack (cursor/PROMPTS.md).
