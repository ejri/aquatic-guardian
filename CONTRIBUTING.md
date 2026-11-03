# Contributing

Contributions are welcome from scientists, engineers, lawyers, officials, Indigenous knowledge holders and members of the public.

## What we need most

- The 16-case **PLUMES 2.0** near-field benchmark (register item P-3; guide in `benchmarks/plumes2/`).
- Species-specific thermal thresholds and welfare parameters to replace placeholders (B-2).
- Corrections to the instrument tracker, with a primary-source link.
- Translations of the framework and model language.

## Rules for changes

1. **Physics and ecology:** every new equation arrives with a test that reproduces a published value or demonstrates the property on synthetic data with known truth, and a row in `docs/VERIFICATION.md`. Never loosen a tolerance to make a test pass.
2. **Engine parity:** changes to `src/aquatic_guardian/screening.py` ↔ `app/engine.js`; changes to `python/plumes2py/` ↔ `site/js/plumes2.js` (`tests/parity.test.mjs`).
3. **Policy text:** cite the instrument and its status date. Mark enacted law, proposed bills and guidance as such.
4. **Uncertainty:** unreviewed values are labelled `placeholder` / `verify` and cannot be used in a flag that tells a user something passes.
5. **Website:** edit `web/parts/*.html` (and Live ocean / Lab / Learn via `tools/integrate_v1.py`), then `python app/build.py`. Do not invent thresholds or legal citations.
6. **Single sources of truth:** see the table in `AGENTS.md`.

## Before opening a pull request

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
pip install -e ./python
python app/build.py --check
pytest -q
cd python && pytest -q
node tests/parity.test.mjs
```

Update `docs/VERIFICATION.md` and `CHANGELOG.md` when behaviour changes. Note anything a human expert still has to check.

Use the issue and pull-request templates under `.github/`.
