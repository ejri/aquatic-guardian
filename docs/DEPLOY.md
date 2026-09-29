# Deploying the website

The public site is two static files, `site/index.html` and `site/404.html`, both built
from `web/parts/` by `app/build.py`. Nothing is compiled on the host. Phase 1
(*Governing the Ocean Server Farm*) used Netlify, so these notes are for Netlify;
any static host that can set response headers will do.

Nobody has deployed this yet. The steps below have not been run, so treat the
dashboard labels as a guide rather than a transcript.

## What the repository already provides

| File | Purpose |
|---|---|
| `netlify.toml` | `publish = "site"`, empty build command, security headers |
| `site/index.html` | the whole site: framework, model language, tracker, screening tool |
| `site/404.html` | not-found page in the same style, links home |
| `.github/workflows/ci.yml` | runs `python app/build.py --check`, so a stale `site/` fails CI before it can ship |

Because Netlify runs no build, the committed `site/index.html` is what visitors get.
Always run `python app/build.py` and commit the result in the same change as any
edit to `web/parts/`, `app/engine.js`, `data/` or `policy/model-language/`.

## Connect the repository

1. Push the repository to GitHub (`ejri/aquatic-guardian`).
2. Sign in at app.netlify.com, then choose **Add new site → Import an existing project**.
3. Pick **GitHub**, authorise Netlify, and select `ejri/aquatic-guardian`.
4. Leave the build settings as Netlify reads them from `netlify.toml`: branch `main`,
   build command empty, publish directory `site`. Do not let the UI substitute a
   build command; if it pre-fills one, clear it.
5. Deploy. The first deploy gives a `*.netlify.app` address.
6. In **Site configuration → Build & deploy → Deploy contexts**, keep deploy previews on
   for pull requests. Previews are useful for reviewing `web/parts/` changes.

## Check the deploy

- Open the site and confirm the fonts load, the screening tool returns numbers, and
  the tracker fills in.
- Visit a path that does not exist (for example `/nope`) and confirm the 404 page appears.
- In the browser's network panel, confirm the only third-party requests are to
  `fonts.googleapis.com` and `fonts.gstatic.com`.
- In the console, confirm no Content-Security-Policy violations are reported. If the
  policy blocks something, fix the page rather than widening the policy; the site is
  meant to be self-contained.
- Run `pytest -m site` locally against the built file (see below); it is the same
  page Netlify serves.

## Custom domain

1. **Domain management → Add a domain** and enter the domain you control.
2. If the domain is registered elsewhere, Netlify shows either name servers to delegate
   to, or the `A`/`CNAME` records to add at your registrar. Delegating name servers is
   simpler; keeping your registrar's DNS is better if other services use the domain.
3. Wait for DNS to propagate, then let Netlify provision the Let's Encrypt certificate
   (**Domain management → HTTPS → Verify DNS configuration**).
4. Turn on **Force HTTPS** once the certificate is issued.
5. Set the primary domain so the other name redirects to it rather than serving a duplicate.

Whoever owns the Sentient Futures domains should make this call; the project is
presented as a Sentient Futures project, and the Phase 1 site lives at
`oceanic-datacenters-governance.netlify.app`.

## Running the browser checks locally

```bash
pip install -e ".[site]"
python -m playwright install chromium
npm install                     # axe-core, injected from node_modules by the test
pytest -m site
python scripts/screenshots.py   # refresh docs/screenshots/
```

`tests/test_site.py` blocks the Google Fonts requests so it works offline, and fails on
any other console error, on horizontal scroll at 390 px, on an unlabelled input, and on
any serious or critical axe-core violation under the WCAG 2.2 AA tag set.

## Still needs a person

- Netlify and DNS accounts, and the decision about which domain to use.
- Confirming with Sentient Futures how the site is linked from their own pages.
