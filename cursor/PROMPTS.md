# Building Aquatic Guardian in Cursor: prompt pack

Run these in order in Cursor's Agent mode. Each prompt is self-contained. Paste it, let the agent work, then check the "Before you move on" line yourself. The rules in `.cursor/rules/` and `AGENTS.md` load automatically and carry the project's invariants, so the prompts don't repeat them.

Tips:
- Start each phase in a new chat so the context stays clean.
- For phases 3, 4 and 7, switch to plan mode first, approve the plan, then let it execute.
- Commit after every phase that ends green.

---

## Phase 0. Open and verify the seed repository

Unzip `aquatic-guardian-v0.1.0.zip`, then in Cursor choose File > Open Folder and select `aquatic-guardian/`.

```text
You are working in the Aquatic Guardian repository. Read AGENTS.md, README.md and docs/VERIFICATION.md first.

Then set up and verify the project:
1. Create a Python virtual environment in .venv and install the package with `pip install -e ".[test]"`.
2. Confirm Node 18+ is available (needed for the engine parity test). If it is missing, tell me how to install it for my OS and stop.
3. Run `pytest -q` and `python app/build.py --check`. Both must pass. Report the test count.
4. Initialise git if needed, check that .gitignore covers .venv, caches, build output and node_modules, and make a first commit "Seed: Aquatic Guardian 0.1.0".
5. Give me a short map of the repository in your own words: what each top-level folder is for and which files are single sources of truth.

Do not change any code or content in this phase.
```

**Before you move on:** 40 tests pass and the build check is clean.

---

## Phase 1. Publish to GitHub with working CI

```text
Prepare the repository for publication on GitHub.

1. Replace every `<org>` placeholder (README.md, CITATION.cff, notebooks/INTEGRATION.md, site/parts/2_body.html, schemas/*.json $id values) with the GitHub organisation or user name I give you here: [ORG_NAME]. Repository name: aquatic-guardian.
2. Rebuild with `python app/build.py` so the site and package resources pick up the change.
3. Check .github/workflows/ci.yml: it must install the package, set up Node 20, run pytest and run `python app/build.py --check` on Python 3.10 and 3.12. Fix anything that would fail on a clean runner.
4. Add .github/ISSUE_TEMPLATE/ with three templates: "Tracker correction" (instrument id, what changed, primary-source link, date checked), "Scientific issue" (module, expected vs observed, source), and "Model language suggestion" (clause id, jurisdiction, proposed text, rationale).
5. Add a pull request template with the Definition of Done checklist from AGENTS.md.
6. Run the tests and the build check, then show me the exact git commands to create the remote and push. Do not push without my confirmation.
```

**Before you move on:** CI is green on GitHub after the first push.

---

## Phase 2. Connect the rebuilt Colab notebooks

First copy the three rebuilt notebooks (Thermal-Tidal 53 cells, Aquatic Monitoring 46 cells, Aquaculture Vision 32 cells) into `notebooks/`.

```text
Integrate the three notebooks in notebooks/ with the aquatic_guardian library, following notebooks/INTEGRATION.md and .cursor/rules/40-notebooks.mdc.

For each notebook:
1. Read the whole notebook first and list every cell that re-implements something the library provides (plume dilution, tidal excursion, upwind transport, DO, ammonia, mixing-zone test, occupancy, image formation, polarisation, Kalman trade-off, TGC growth, carrying capacity). Show me that list before editing.
2. Replace those implementations with library calls. Keep the teaching text, figures and vetting assertions. Where the notebook's old result differs from the library's, do not hide it: add a markdown cell explaining the difference and which correction in docs/CORRECTIONS.md accounts for it.
3. Replace ad-hoc JSON with ag.handoff.make/write/read so every handoff validates against schemas/notebook-handoff.schema.json. Run order stays thermal, then monitoring and aquaculture; aquaculture returns recommended_loop_inlet_ceiling_c to thermal.
4. Make the first code cell install the library. For local runs use `pip install -e ..`; for Colab use the pinned GitHub tag. Detect which environment you are in.

Then add tests/test_notebooks.py that executes all three notebooks headlessly with nbclient (CPU, synthetic data, 15-minute timeout each), in run order, and asserts the handoff files exist and validate. Mark it with a pytest marker `slow` and add a separate CI job that runs it.

Run everything and report: cells changed per notebook, any result that moved and why, runtime per notebook.
```

**Before you move on:** all three notebooks execute headlessly and the handoff files validate.

---

## Phase 3. Independent near-field benchmark (register item P-3)

Use plan mode.

```text
Register item P-3 in docs/VERIFICATION.md says the near-field dilution coefficients (0.089 point plume, 0.38 line plume, 5.6 jet decay) need a benchmark. Build the benchmark infrastructure. Do not change the coefficients in this phase.

1. Create benchmarks/integral_jet.py: an independent integral model of a round buoyant jet in a stagnant, unstratified ambient using the entrainment formulation of Morton, Taylor and Turner (1956) with a variable entrainment coefficient that transitions from jet to plume values. Use entrainment coefficients from a named source (for example Fischer et al. 1979 or Lee and Chu 2003). State the source in the docstring. If you are not certain of a value, make it a parameter and flag it in your reply rather than guessing.
2. Integrate it with scipy's solve_ivp, returning centreline dilution versus height.
3. Create benchmarks/compare_near_field.py that sweeps port diameter, flow, reduced gravity and depth across the ranges in tests/test_engine_parity.py, runs both the library asymptotes and the integral model, and writes benchmarks/results/near_field_comparison.csv plus a plot of the ratio of the two against z/l_M.
4. Create benchmarks/visual_plumes/: a script that writes Visual Plumes (UM3) input decks for the same cases, and a README explaining how a person runs them in EPA's Visual Plumes (a Windows application) and saves outputs to benchmarks/visual_plumes/outputs/ in a specified CSV format. Add a loader that reads those outputs into the comparison when present.
5. Add tests/test_benchmark_integral.py: the integral model reproduces pure-jet and pure-plume similarity scaling in the limits (dilution proportional to z for a jet and to z^(5/3) for a plume) within a stated tolerance.
6. Write docs/BENCHMARK_P3.md summarising the comparison: where the asymptotic envelope agrees with the integral model, where it is conservative, and where it is not. Keep P-3's status as "Needs benchmark" until Visual Plumes outputs are in; say so.

Report the headline agreement numbers and any case where the library is less conservative than the integral model.
```

**Before you move on:** you have the comparison CSV and know whether the screening envelope is conservative across the tested range. A person still needs to run Visual Plumes.

---

## Phase 4. Close the text-check items (W-4 and R-2)

You need the primary sources open: Bower and Bidwell (1978) Table for un-ionised ammonia in seawater, and the current California Thermal Plan text.

```text
Register items W-4 (seawater ammonia correction) and R-2 (California Thermal Plan values) need checking against primary text. I will transcribe the source values; you build the checks.

1. Create data/checks/bower_bidwell_1978.csv with columns temperature_c, ph, salinity_psu, unionised_percent, source_page. Leave it with a header and three example rows marked "TRANSCRIBE" so I know the format.
2. Add tests/test_primary_sources.py that, for every non-placeholder row, compares water_quality.unionised_fraction to the table within a tolerance you justify from the table's printed precision. Skip with a clear message while rows still say TRANSCRIBE.
3. Create data/checks/ca_thermal_plan.md where I paste the exact text of the new-discharge coastal provisions with the document date. Add a test that parses the degree values (Fahrenheit) and the distance and compares them to criteria.ca_thermal_plan_new_coastal().
4. When both tests pass with real data, update docs/VERIFICATION.md rows W-4 and R-2 to "Published value" and cite page numbers. If any comparison fails, do not adjust tolerances: report the discrepancy and propose which of the formula, the table transcription or the rule text is wrong.
```

**Before you move on:** W-4 and R-2 are either verified with page citations or have a documented discrepancy.

---

## Phase 5. Deploy the website

```text
Deploy site/index.html as the public Aquatic Guardian website on Netlify (Phase 1 also used Netlify).

1. Restructure so only built output is published: move site/parts/ to web/parts/, keep the built page at site/index.html, and update app/build.py, the rules file .cursor/rules/30-site.mdc and AGENTS.md accordingly. Tests and the build check must still pass.
2. Add netlify.toml with publish = "site", no build command (CI guarantees the built file is fresh), and security headers: a Content-Security-Policy allowing only 'self', inline scripts and styles, fonts.googleapis.com for styles and fonts.gstatic.com for fonts; plus Referrer-Policy, X-Content-Type-Options and Permissions-Policy.
3. Add a 404.html in the same visual style that links home.
4. Add tests/test_site.py using Playwright (Chromium) that loads site/index.html and checks: no console errors other than blocked fonts; no horizontal scroll at 390 px; every input has a label; the screening tool produces results in Public, Officials and Technical modes; changing the hero IT load changes the flow; the jurisdiction tabs switch with arrow keys; dark mode renders. Also run axe-core (inject it from a local node_modules copy, not a CDN) and fail on serious or critical violations. Mark these tests `site` and add a CI job for them.
5. Take desktop (1366 px) and mobile (390 px) screenshots of each section into docs/screenshots/, review them yourself and list anything that looks wrong before fixing it.
6. Tell me the steps to connect the GitHub repo to Netlify and set a custom domain. Do not create accounts or deploy on my behalf.
```

**Before you move on:** site tests and axe pass; screenshots look right on phone and desktop.

---

## Phase 6. Make the tool jurisdiction-aware

```text
The screening tool currently offers three temperature rules: Washington marine (WAC 173-201A-210), California Thermal Plan (new coastal) and a permit-specific custom increment. Extend it so a user can pick a jurisdiction and get the right defaults, without inventing any rule.

1. Add a `jurisdictions` section to data/criteria.json listing, per jurisdiction, which temperature rule applies, its legal status and source, and which intake rule applies. Include only rules the repository already documents with a source. For British Columbia, the EU and Oregon, where the numeric rule depends on the permit or on guidance not yet transcribed, map to "custom" with an explanatory note and `"verify": true`.
2. Implement the lookup in Python (criteria.py) and mirror it in app/engine.js. Extend tests/test_engine_parity.py to cover every jurisdiction.
3. In the site, add a "Jurisdiction" select at the top of the Rules fieldset. It sets the rule and shows the note and status. Officials mode shows the source citation beside the draft permit conditions.
4. Update the flags so the §316(b) and 40 CFR 125.84 flags only appear for US jurisdictions, and a Fisheries Act s.36 note appears for Canadian ones.
5. Rebuild, run all tests, update VERIFICATION.md and CHANGELOG.md.
```

**Before you move on:** parity passes for every jurisdiction and no flag cites a law that doesn't apply there.

---

## Phase 7. Policy briefs for officials

Use plan mode.

```text
Officials need short documents they can print or attach, generated from the same sources as the site.

1. Create app/briefs.py that builds one brief per tab in the model-language library (US federal, US states, permits, EU, Canada, international and UK). Each brief: a one-paragraph problem statement drawn from policy/FRAMEWORK.md section 1, the jurisdiction's status paragraph, the relevant rows of data/instruments.json, the clauses verbatim from the markdown markers, the relevant rows of policy/RECOMMENDATIONS.md, and a footer with version, date, licence and the screening disclaimer.
2. Output Markdown to briefs/ and, if pandoc is installed, also PDF and DOCX. Never retype clause text; read it from the markers.
3. Add a test that every clause id in policy/model-language appears in exactly one brief and that the text matches byte for byte.
4. Add a "Download briefs" subsection to the Open source section of the site that links to the brief files on GitHub (the page itself must still make no network requests).
5. Keep each brief to two printed pages where possible; tell me which ones run over.
```

**Before you move on:** briefs regenerate from source and the clause-match test passes.

---

## Phase 8. Tracker upkeep

```text
Make the policy tracker easy to keep current.

1. Add a `last_checked` date and a `sources` array (url, title, accessed date) to every entry in data/instruments.json. Fill `sources` only with URLs I provide or that are already cited in the repository; leave it empty and set "verify": true otherwise. Do not invent URLs.
2. Add scripts/tracker_report.py that lists entries whose last_checked is older than 60 days, entries with verify=true, and dates that have passed but whose status still describes them as future events.
3. Add a scheduled GitHub Action (weekly) that runs the report and opens or updates a single issue titled "Tracker review due" with the output.
4. In the site's tracker, show "last checked" per row and a note at the top when any row is stale.
5. Update the schema of the tracker in a new schemas/instruments.schema.json and validate the data file in tests.
```

**Before you move on:** the report runs locally and the site shows last-checked dates.

---

## Phase 9. Release 0.1.0 publicly

```text
Prepare the public 0.1.0 release.

1. Run the full test suite, including slow and site tests, and the build check. Stop and report if anything fails.
2. Review CHANGELOG.md, CITATION.cff and README.md for accuracy against what is actually in the repository. List any claim that is not backed by a file or a test.
3. Add a .zenodo.json with title, description, creators (from CITATION.cff), licence and keywords, so the GitHub–Zenodo integration mints a DOI on release.
4. Draft release notes: what the framework is, the four deliverables, verification status (what is verified, what needs a benchmark, what is placeholder), and how officials and researchers can contribute.
5. Show me the commands to tag v0.1.0 and create the GitHub release. Do not run them without my confirmation.
```

---

## Reusable prompts

### Audit before sharing anything

```text
Audit the repository for claims that outrun the evidence. Check every number, legal status, date and citation in policy/, site/parts/, README.md and docs/ against data/instruments.json, data/criteria.json, docs/VERIFICATION.md and the tests. Produce a table: claim, file and line, backing source or test, verdict (backed, needs source, wrong). Do not edit anything; I will decide what to change.
```

### Add a new jurisdiction's model language

```text
Add model language for [JURISDICTION] to policy/model-language/[file].md, following .cursor/rules/20-policy.mdc. I will provide the instruments and their status: [PASTE]. Draft clauses that attach to those instruments using their own definitions. Add tracker entries to data/instruments.json with "verify": true until I confirm sources. Add the file to GROUPS in app/build.py, rebuild, and run the tests.
```

### Add a new scientific module

```text
Add [MODULE] to src/aquatic_guardian/ implementing [EQUATION OR METHOD] from [SOURCE]. Follow .cursor/rules/10-physics.mdc: docstring with source and validity range, a test that reproduces a published value from that source (tell me which value and page), a VERIFICATION.md row, and a CHANGELOG entry. If the method feeds the screening tool, mirror it in app/engine.js and extend the parity test.
```

### Fix a bug without papering over it

```text
[DESCRIBE THE SYMPTOM]. Diagnose from first principles before changing code: state the equation or data path involved, show where the observed value departs from the expected one, and explain the cause. Then fix the cause, add a regression test that fails before the fix and passes after, and note it in CHANGELOG.md. Do not loosen tolerances or suppress warnings.
```

---

## What Cursor cannot do for you

- Run EPA Visual Plumes (Windows desktop software) for the P-3 benchmark.
- Confirm legal text, cosponsor counts or BC Hydro round results; those need a person reading the primary source.
- Supply species thresholds and welfare parameters; those need species specialists and a fish-health veterinarian.
- Decide how the project is branded as Sentient Futures; confirm that with them before the site goes public.
