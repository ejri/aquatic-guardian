# Learn computer vision — Aquatic Guardian tab

A standalone teaching tab for the Aquatic Guardian website: nine modules that take early learners from pixels to
defensible claims about aquatic wildlife, each with a Google Colab notebook, plus capstones that map onto the
project notebooks.

**Pinned deps:** [`requirements.txt`](requirements.txt). CI: `.github/workflows/learn-notebooks.yml` (nbmake on CPU).

| Module | Open in Colab |
|---|---|
| CV01 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ejri/aquatic-guardian-learning-modules/blob/main/notebooks/CV01_images_are_arrays.ipynb) |
| CV02 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ejri/aquatic-guardian-learning-modules/blob/main/notebooks/CV02_how_water_changes_images.ipynb) |
| CV03 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ejri/aquatic-guardian-learning-modules/blob/main/notebooks/CV03_classical_image_processing.ipynb) |
| CV04 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ejri/aquatic-guardian-learning-modules/blob/main/notebooks/CV04_learning_to_classify.ipynb) |
| CV05 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ejri/aquatic-guardian-learning-modules/blob/main/notebooks/CV05_robustness_and_reporting.ipynb) |
| CV06 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ejri/aquatic-guardian-learning-modules/blob/main/notebooks/CV06_neural_networks_and_cnns.ipynb) |
| CV07 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ejri/aquatic-guardian-learning-modules/blob/main/notebooks/CV07_detection_measurement_calibration.ipynb) |
| CV08 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ejri/aquatic-guardian-learning-modules/blob/main/notebooks/CV08_tracking_over_time.ipynb) |
| CV09 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ejri/aquatic-guardian-learning-modules/blob/main/notebooks/CV09_from_pixels_to_claims.ipynb) |

Licences: notebooks GPL-3.0; NOAA photos public domain; see `images/ATTRIBUTION.md`.

## What's in this folder

| Path | What it is |
|---|---|
| `learn.html` | The tab. One self-contained page: lessons, a learning-path finder, five interactive demos, capstones, instructor notes, glossary. |
| `notebooks/` | Nine Colab notebooks, saved without outputs. |
| `source/` | The Python scripts that generate the notebooks, and `run.py`, which executes them as a test. Edit these, not the notebooks. |

## Adding the tab to the site

**As its own page.** Put `learn.html` and the `notebooks/` folder side by side and link to `learn.html` from the
site's navigation. The download buttons work immediately.

**Inside an existing page.** Copy three things from `learn.html` into the host page: the `<style>` block, the
`<div id="ag-learn">…</div>` block, and the `<script>` block at the end. Every style is scoped to `#ag-learn`, so it
won't affect the rest of the site. The colour tokens at the top of the `<style>` block can be mapped to the site's
palette. The page follows the reader's light or dark setting; `data-theme="dark"` or `data-theme="light"` on `<html>`
or on `#ag-learn` overrides it.

**One-click Colab buttons.** Push `notebooks/` to a public GitHub repository, then set the attribute on the outer
element, for example:

```html
<div id="ag-learn" data-colab-base="https://colab.research.google.com/github/OWNER/REPO/blob/main/notebooks/" data-notebook-path="notebooks/">
```

With `data-colab-base` empty, each module shows a download button and a one-line instruction to upload the file
to Colab instead. `data-notebook-path` is where the page looks for the `.ipynb` files for download.

**Linking to a module.** `learn.html#m07` opens Module 07 directly.

**External requests.** The page loads the Atkinson Hyperlegible font from Google Fonts and nothing else. If the
site's content-security policy blocks Google Fonts, it falls back to system fonts.

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
cd source
mkdir -p out
python cv07.py                      # regenerates out/CV07_....ipynb
pip install nbformat nbclient ipykernel torch torchvision   # once
python run.py out/CV07_*.ipynb      # executes it and prints every output; fails loudly on any error
cp out/CV07_*.ipynb ../notebooks/
```

`nbcommon.py` holds the shared synthetic-scene generator, the image-formation model and the project's `degrade()`
utility. Several numbers quoted on the course page come from these test runs (for example the leakage
demonstration in 04 and the occupancy false-alarm rates in 09). If you change a notebook, re-run it and check the
matching sentence on the page. Module 06 trains small networks, so its numbers can move by a few points between runs
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
