# Learn route (#/learn), rebuilt for the Aquatic Guardian site

Three files replace the current Learn route. They are built on the site's own tokens and components
(`.pagehead`, `.block`, `.inst`, `.btn`, `.jur`, `.seg`, `.steps-nav`, `details.faq`), so the page now looks and
behaves like the rest of the site.

## Why the old page looked broken

It was written as a standalone page with its own fonts and colours, and several of its class names were also
site components: `.hero` (full-height dark hero with a gradient overlay), `.seg` (boxed segmented control),
`.lab` (the Lab's two-column grid, which squeezed the Kalman demo into a 14rem column), `.nb` and `.field`.
Every class this rebuild adds starts with `lc-`, and every rule is scoped to `[data-route="learn"]`. Site
components are reused on purpose, never restyled.

## Install

1. In `index.html`, replace everything from `<!-- ================= LEARN CV ================= -->` up to
   (not including) `<footer class="site">` with the contents of `learn.html`.
2. Replace the site's `learn.css` and `learn.js` with the files here. Keep the existing `<link>` and `<script>`
   tags; `learn.js` must load after the router script, as before.
3. Nothing else changes. `learn.js` registers `AGU.inits.learn` and `AGU.onRoute.learn`, like `observatory.js`.

## Addresses

| Address | Opens |
|---|---|
| `#/learn` | The overview |
| `#/learn/tour` | The ten-minute tour |
| `#/learn/five` | Five questions to ask about any camera count |
| `#/learn/course` | Starting points and the module map |
| `#/learn/m01` … `#/learn/m09` | A module page |
| `#/learn/teach`, `#/learn/capstones`, `#/learn/glossary`, `#/learn/faq` | Those sections |

## What is on the page

- **Ten-minute tour (no code).** Five steps on one live camera instrument: pixels are numbers (tap to read a
  pixel), water steals colour, how a detector finds a fish (Picture, Difference, Mask, Boxes), missing isn't
  gone, and asking good questions.
- **Before you trust a camera count.** Five questions for anyone reading a news story or a permit filing, each
  linked to the module that explains it.
- **Course.** Six starting points (including "Policy, no coding"), a module map with progress, and a page per
  module: objectives, lesson, a live demo, common mistakes, a real-world example with its source, the notebook
  with Open in Colab, a three-question quiz with explanations, further reading, and previous/next.
- **Demos.** Underwater camera (Modules 01, 02 and the tour), filter lab (03), saying "I don't know" (04),
  results by condition (05), model comparison (06), flat camera window (07), Kalman tracking (08),
  seen versus there (09). All synthetic and computed in the page; no network requests.
- **Teach with this.** A one-hour public session plan, a printable "Count, then detect" worksheet that uses the
  Live ocean cameras and their Detect animals button, and a five-week course outline.
- **Capstones, plain-language glossary with a filter, and an FAQ.**

## Editing content

All lesson text, quizzes, sources, tour steps, paths and glossary entries are in the CONTENT block at the top of
`learn.js`. `#lc` attributes: `data-colab-base` and `data-github-base` point at
`ejri/aquatic-guardian-learning-modules` (`notebooks/` on `main`); `data-download-base` is the built
site’s `notebooks/` folder. Wildlife frames for the in-page cameras live in
`learning_materials/aquatic-guardian-learn-cv/images/` and are copied to `site/img/learn/`.

## Storage and privacy

Progress, quiz answers and the chosen starting point are kept in `localStorage` under `agl-path`, `agl-done` and
`agl-quiz`, on the reader's device only. The page sends nothing anywhere.

## Checked

Rendered inside the saved site at desktop and phone widths, in light and dark mode, with no script errors and no
horizontal scrolling on a 390 px screen. Moving between Learn and other routes and back works. Each tour step's
claim was checked against what the detector reports at that step.
