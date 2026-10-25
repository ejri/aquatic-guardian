# Learn computer vision — Aquatic Guardian

Nine modules that take early learners from pixels to defensible claims about aquatic wildlife,
each with a Google Colab notebook, plus capstones that map onto the project notebooks.

The live site tab is `#/learn`. Do not edit the old standalone `learn.html` at the root of this
folder: that page is a leftover draft. The site reads the rebuilt route.

## What's in this folder

| Path | What it is |
|---|---|
| `learn-route/` | **Source of the live `#/learn` tab.** `learn.html` is the route block; `learn.css` and `learn.js` are mirrored into `site/` by `python app/build.py`. |
| `learn-route/README.md` | Addresses (`#/learn/m03`, `#/learn/tour`, …) and what each section does. |
| `aquatic-guardian-learn-cv/notebooks/` | Nine Colab notebooks, saved without outputs. Copied to `site/notebooks/` at build. |
| `aquatic-guardian-learn-cv/source/` | Python scripts that generate the notebooks, and `run.py`, which executes them as a test. Edit these, not the notebooks. |
| `learn.html`, `learn.css`, `learn.js` | Old standalone draft. Not used by the build. |

## How the site is built

```bash
python app/build.py          # injects learn-route/learn.html; copies CSS, JS and notebooks into site/
python app/build.py --check  # fails if site/index.html, site/css/learn.css, site/js/learn.js or site/notebooks/ are stale
```

`tools/integrate_v1.py` inserts `learn-route/learn.html` as the single `data-route="learn"` block.
Lesson copy, quizzes and sources live in `learn-route/learn.js`. Edit those files, then rebuild.

**Linking to a module.** `#/learn/m07` opens Module 07.

**Running a notebook.** Each module has **Open in Colab**, which loads from the public repository
https://github.com/ejri/aquatic-guardian-learning-modules (path `notebooks/`). Choose File → Save a
copy in Drive, then Runtime → Run all. Real wildlife frames are in that repo’s `images/` folder.

**Photographs.** `learn-route/images/` (mirrored to `site/img/learn/` and to the public repo). Live-camera
stills plus NOAA public-domain photographs. See `learn-route/images/ATTRIBUTION.md`.

**External requests.** The site tab uses the host page fonts. The page itself does not fetch
lesson content from the network.

## The modules

| # | Module | Prepares for | Test run time (CPU) |
|---|---|---|---|
| 01 | Images are arrays of numbers | everything | 3 s |
| 02 | How water changes an image | robustness, detection range, Module 09 | 3 s |
| 03 | Classical image processing | Mentee 2 segmentation and measurement | 3 s |
| 04 | Learning to classify, without fooling yourself | Mentee 1 baseline, splits, metrics, abstention | 5 s |
| 05 | Robustness, shift and honest reporting | Mentee 1 robustness, data/model cards, event schema | 9 s |
| 06 | Neural networks and CNNs (PyTorch) | Mentee 1 CNN reference and transfer learning | 47 s |
| 07 | Detection, measurement and calibration | Mentee 2 calibration, morphometrics, biomass | 5 s |
| 08 | Tracking over time | tracking, behaviour, camera siting | 3 s |
| 09 | From pixels to defensible claims | occupancy correction, findings, ethics | 5 s |

Times are from executing each notebook top to bottom in a CPU-only test environment. Colab's free tier is in the
same range. Every notebook generates its own synthetic data, so no dataset or GPU is needed. Real-data paths are
included and switched off with `RUN_REAL_DATA = False`, matching the project notebooks.

Paths offered on the page: new to coding with images (all nine, about 20 h); Python and ML but not images
(02, 03, 05, 07, 08, 09); monitoring workstream (01, 02, 04, 05, 06, 09); aquaculture workstream
(01, 02, 03, 05, 07, 08, 09); tracking and behaviour (01, 03, 07, 08, 09); policy, no coding (pages and demos for
02, 04, 05, 09).

## Changing a notebook

```bash
cd aquatic-guardian-learn-cv/source
mkdir -p out
python cv07.py                      # regenerates out/CV07_....ipynb
pip install nbformat nbclient ipykernel torch torchvision   # once
python run.py out/CV07_*.ipynb      # executes it and prints every output; fails loudly on any error
cp out/CV07_*.ipynb ../notebooks/
```

Then run `python app/build.py` so `site/notebooks/` matches.

`nbcommon.py` holds the shared synthetic-scene generator, the image-formation model and the project's `degrade()`
utility. Several numbers quoted on the course page come from these test runs (for example the leakage
demonstration in 04 and the occupancy false-alarm rates in 09). If you change a notebook, re-run it and check the
matching sentence in `learn-route/learn.js`. Module 06 trains small networks, so its numbers can move by a few points between runs
and machines; the page words those as approximate.

## Findings about the project notebooks

These came up while building the course and are written into the capstones.

1. **Condition factor in the Mentee 2 aquaculture notebook (Tasks 6 and 8).** Mass is estimated from length with
   `W = aL^b`, then Fulton's `K = 100W/L^3` is computed from that estimated mass. With `b = 3` every fish gets
   `K = 100a = 1.20`, the exact lower edge of the placeholder band, so `flag_K` can't respond to real condition.
   Confirmed by running the notebook. Module 07 teaches the problem; Capstone B asks for a fix.
2. **Robustness tests that use only `degrade()` can mislead.** A CNN that standardises each frame scored about
   0.93–0.99 under `degrade()` turbidity and low light but about 0.7 on fish made physically farther away with the
   image-formation model. `degrade()`'s turbidity step is nearly an affine change to the whole frame, which
   per-image normalisation cancels. Capstone A asks for results under two degradation models.
3. **Notebook versions.** Capstone task numbers follow the six-week versions of the Mentee 1 and Mentee 2 notebooks.
   Tracking and occupancy-correction sections in later versions map to Modules 08 and 09.

## Known simplifications

All scenes and surveys are synthetic. Attenuation coefficients, turbidity units and detection parameters are
illustrative teaching values, not site measurements. Species parameters and welfare bands remain placeholders to be
set with aquatic-science input, as in the project notebooks.
