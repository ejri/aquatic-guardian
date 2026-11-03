# Security

## Scope

Aquatic Guardian is a **screening and education** toolkit. It does not handle end-user accounts or payment. The optional `relay/` service proxies allow-listed ocean-data APIs and can run vision workers only when an operator permission is recorded.

## Reporting a vulnerability

Please open a **private** security advisory on [github.com/ejri/aquatic-guardian](https://github.com/ejri/aquatic-guardian/security/advisories/new), or email the maintainers listed in `CITATION.cff` / the GitHub repository. Do not file a public issue for an unfixed vulnerability.

Include: affected path or URL, steps to reproduce, and impact (data exposure, XSS, SSRF via the proxy, etc.).

## Notes for operators

- Keep `relay/permitted_streams.json` empty until written permission exists for each camera (`docs/STREAMS.md`).
- Do not set `AG_RUN_WORKERS=1` without reviewing that file.
- Netlify CSP ships as Report-Only in `netlify.toml`; tighten after checking for violations.
- Do not commit API keys; use repository secrets / Fly secrets for `YOUTUBE_API_KEY`, `ONC_TOKEN`, and similar.
