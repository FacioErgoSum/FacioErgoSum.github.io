# facioergosum.com — self-hosted static mirror

Static export of the Squarespace site **facioergosum.com**, captured 2026-06-10, for self-hosting on GitHub Pages.

## Contents
- `index.html` + per-page `*/index.html` folders — server-rendered HTML for all 26 pages
- `assets/` — all images, CSS, and other media (~2,300 files), with page HTML rewritten to reference them locally
- `CNAME` — custom domain config for GitHub Pages (`facioergosum.com`)
- `.nojekyll` — tells GitHub Pages to serve files as-is (no Jekyll processing)
- `_mirror.py` — the script used to capture the site (kept for reproducibility)

## Hosting on GitHub Pages
1. Push this repo to GitHub.
2. Repo **Settings → Pages → Build and deployment → Source: Deploy from a branch**, branch `main` / root.
3. Once you're ready to move the domain, point `facioergosum.com` DNS at GitHub Pages and the `CNAME` file will take effect.

## Caveats
- Links are root-relative, so the site is intended to be served at the domain root (custom domain), not a `/repo/` subpath.
- A handful of Squarespace runtime scripts still reference `static1.squarespace.com`; content and images are fully local, but some dynamic behaviors depended on Squarespace's JS.
