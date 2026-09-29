"""Capture docs/screenshots/ from the built site, for design review.

    python -m playwright install chromium
    python scripts/screenshots.py

One image per section at 1366 px (desktop) and 390 px (phone), plus the screening
tool in each mode, dark mode and the 404 page. Google Fonts are allowed to load
here so the review sees the real typography; tests/test_site.py blocks them.
Nothing in the published site depends on this script.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
SECTIONS = ["top", "mission", "framework", "language", "tracker", "tool", "evidence", "source"]
WIDTHS = {"desktop": 1366, "mobile": 390}


def prepare(page) -> None:
    page.wait_for_selector("#results .summary")
    page.evaluate("() => document.fonts.ready")
    # The sticky header would otherwise sit over the top of each element screenshot.
    page.add_style_tag(content="header.site{position:static!important}")


def shoot(page, target: str, name: str) -> None:
    el = page.locator(target)
    el.scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    el.screenshot(path=str(OUT / f"{name}.png"), animations="disabled")
    print("wrote", (OUT / f"{name}.png").relative_to(ROOT))


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('playwright is not installed: pip install -e ".[site]"', file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    index, notfound = (ROOT / "site" / "index.html").as_uri(), (ROOT / "site" / "404.html").as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for label, width in WIDTHS.items():
            ctx = browser.new_context(viewport={"width": width, "height": 900},
                                      device_scale_factor=1)
            page = ctx.new_page()
            page.goto(index)
            prepare(page)
            for s in SECTIONS:
                shoot(page, "#" + s, f"{label}-{s}")
            for mode in ("official", "technical"):
                page.click(f'.modes button[data-mode="{mode}"]')
                page.wait_for_selector("#results .summary")
                shoot(page, "#tool", f"{label}-tool-{mode}")
            page.goto(notfound)
            page.evaluate("() => document.fonts.ready")
            page.screenshot(path=str(OUT / f"{label}-404.png"), animations="disabled")
            print("wrote", (OUT / f"{label}-404.png").relative_to(ROOT))
            ctx.close()

        ctx = browser.new_context(viewport={"width": WIDTHS["desktop"], "height": 900},
                                  device_scale_factor=1, color_scheme="dark")
        page = ctx.new_page()
        page.goto(index)
        prepare(page)
        for s in ("top", "tool", "tracker"):
            shoot(page, "#" + s, f"dark-{s}")
        ctx.close()
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
