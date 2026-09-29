# Contributing

Contributions are welcome from scientists, engineers, lawyers, officials, Indigenous knowledge holders and members of the public.

## What we need most
- A Visual Plumes UM3 or NRFIELD benchmark for the near-field coefficients (register item P-3).
- Species-specific thermal thresholds and welfare parameters to replace placeholders (B-2).
- Corrections to the instrument tracker, with a primary-source link.
- Translations of the framework and model language.

## Rules for changes
1. **Physics and ecology:** every new equation arrives with a test that reproduces a published value or demonstrates the property on synthetic data with known truth, and a row in `docs/VERIFICATION.md`.
2. **Engine parity:** any change to `src/aquatic_guardian/screening.py` must be mirrored in `app/engine.js`; `tests/test_engine_parity.py` enforces this.
3. **Policy text:** cite the instrument and its status date. Mark enacted law, proposed bills and guidance as such.
4. **Uncertainty:** unreviewed values are labelled `placeholder` and cannot be used in a flag that tells a user something passes.

Run `pip install -e ".[test]" && pytest -q && python app/build.py` before opening a pull request.
