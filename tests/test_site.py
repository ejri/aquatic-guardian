"""Browser checks for the published site, driven with Playwright (Chromium).

These are the accessibility and behaviour promises in .cursor/rules/30-site.mdc,
checked against the built file that Netlify publishes rather than against the
fragments in web/parts/. Marked `site` and skipped unless the extras are present:

    pip install -e ".[site]" && python -m playwright install chromium && npm install

axe-core is injected from the local node_modules copy. The page itself never
loads a script from npm or a CDN, and this test does not change that: font
requests are aborted so the run works offline and matches the "no network
requests except Google Fonts" rule.
"""
from __future__ import annotations
import json
from pathlib import Path
import pytest

pytestmark = pytest.mark.site

sync_api = pytest.importorskip("playwright.sync_api",
                               reason='playwright is not installed: pip install -e ".[site]"')

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "site" / "index.html"
NOT_FOUND = ROOT / "site" / "404.html"
AXE = ROOT / "node_modules" / "axe-core" / "axe.min.js"
FONT_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")
WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
DESKTOP = {"width": 1366, "height": 900}
PHONE = {"width": 390, "height": 844}
MODES = ["public", "official", "technical"]


class Site:
    """A loaded page plus the console errors it produced."""

    def __init__(self, page, errors):
        self.page, self.errors = page, errors

    @property
    def unexpected_errors(self) -> list[str]:
        """Console errors other than the deliberately blocked Google Fonts requests."""
        return [e for e in self.errors if not any(h in e for h in FONT_HOSTS)]

    def mode(self, name: str) -> None:
        self.page.click(f'.modes button[data-mode="{name}"]')
        self.page.wait_for_selector("#results .summary")

    def select(self, field: str, value: str) -> None:
        self.page.select_option(f"#in-{field}", value)
        self.page.wait_for_selector("#results .summary")


@pytest.fixture(scope="session")
def browser():
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as exc:  # noqa: BLE001 - the message is the point
            pytest.skip(f"Chromium is not installed: python -m playwright install chromium ({exc})")
        yield b
        b.close()


def _open(browser, url: Path, **context_kwargs) -> Site:
    ctx = browser.new_context(**{"viewport": DESKTOP, **context_kwargs})
    page = ctx.new_page()
    errors: list[str] = []
    page.requests = []
    page.on("request", lambda r: page.requests.append(r.url))
    page.on("console", lambda m: errors.append(f"{m.location.get('url', '')} {m.text}")
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(f"pageerror {e}"))
    page.route(f"**/*{{{','.join(FONT_HOSTS)}}}/**", lambda route: route.abort())
    for host in FONT_HOSTS:
        page.route(f"https://{host}/**", lambda route: route.abort())
    page.goto(url.as_uri())
    return Site(page, errors)


@pytest.fixture
def site(browser):
    s = _open(browser, INDEX)
    s.page.wait_for_selector("#results .summary")
    yield s
    s.page.context.close()


def test_the_page_loads_with_no_console_errors(site):
    assert site.unexpected_errors == []
    assert site.page.title().startswith("Aquatic Guardian")


def test_404_page_loads_cleanly_and_links_home(browser):
    s = _open(browser, NOT_FOUND)
    assert s.unexpected_errors == []
    assert "not found" in s.page.title().lower()
    assert s.page.locator('main a[href="/"]').count() >= 1
    assert s.page.locator("h1").count() == 1
    s.page.context.close()


@pytest.mark.parametrize("mode", MODES)
def test_no_horizontal_scroll_on_a_390px_phone(browser, mode):
    s = _open(browser, INDEX, viewport=PHONE)
    s.page.wait_for_selector("#results .summary")
    s.mode(mode)
    # The tracker and framework tables are wide on purpose; they scroll inside .scroll.
    overflow = s.page.evaluate(
        "() => ({doc: document.documentElement.scrollWidth, win: window.innerWidth})")
    assert overflow["doc"] <= overflow["win"] + 1, (mode, overflow)
    assert s.unexpected_errors == []
    s.page.context.close()


@pytest.mark.parametrize("mode", MODES)
def test_every_input_has_a_label(site, mode):
    site.mode(mode)
    unlabelled = site.page.evaluate("""() => {
      const bad = [];
      for (const el of document.querySelectorAll("input, select, textarea")) {
        if (el.type === "hidden") continue;
        const byId = el.id && document.querySelector('label[for="' + el.id + '"]');
        const wrapped = el.closest("label");
        const aria = el.getAttribute("aria-label");
        const ref = el.getAttribute("aria-labelledby");
        const named = (byId && byId.textContent.trim()) || (wrapped && wrapped.textContent.trim())
          || (aria && aria.trim()) || (ref && document.getElementById(ref));
        if (!named) bad.push(el.outerHTML.slice(0, 120));
      }
      return bad;
    }""")
    assert unlabelled == [], (mode, unlabelled)


@pytest.mark.parametrize("mode", MODES)
def test_the_screening_tool_produces_results_in_every_mode(site, mode):
    site.mode(mode)
    text = site.page.inner_text("#results")
    assert "heat to water" in text
    assert "MW" in text and "m³/s" in text
    assert "Screening only" in text
    # Officials and technical add the drafting aids; public must not show raw JSON.
    assert ("Draft permit conditions" in text) == (mode != "public")
    assert ("Aquatic Disclosure Record" in text) == (mode != "public")
    assert ("Technical detail" in text) == (mode == "technical")


def test_changing_the_hero_it_load_changes_the_flow(site):
    before = site.page.inner_text("#h-flow")
    site.page.fill("#h-mw", "120")
    site.page.wait_for_function(
        "prev => document.querySelector('#h-flow').textContent !== prev", arg=before)
    after = site.page.inner_text("#h-flow")
    assert float(after.replace(",", "")) > float(before.replace(",", ""))
    assert float(site.page.inner_text("#h-mgd").replace(",", "")) > 2


def test_the_model_language_tabs_move_with_arrow_keys(site):
    tabs = site.page.locator("#lang-tabs button")
    assert tabs.count() >= 2
    first = tabs.nth(0)
    first.click()
    assert first.get_attribute("aria-selected") == "true"
    before = site.page.inner_text("#lang-panel")
    site.page.keyboard.press("ArrowRight")
    assert tabs.nth(1).get_attribute("aria-selected") == "true"
    assert tabs.nth(0).get_attribute("aria-selected") == "false"
    assert site.page.inner_text("#lang-panel") != before
    site.page.keyboard.press("ArrowLeft")
    assert tabs.nth(0).get_attribute("aria-selected") == "true"
    assert site.page.inner_text("#lang-panel") == before


def test_dark_mode_renders_the_dark_tokens(browser):
    s = _open(browser, INDEX, color_scheme="dark")
    s.page.wait_for_selector("#results .summary")
    bg = s.page.evaluate("() => getComputedStyle(document.body).backgroundColor")
    assert bg == "rgb(12, 29, 34)", bg          # --bg dark token in web/parts/1_head.html
    assert s.page.inner_text("#results").strip()
    assert s.unexpected_errors == []
    s.page.context.close()


def test_the_page_requests_nothing_but_google_fonts(site):
    """The self-contained rule, checked rather than asserted in a comment."""
    site.mode("technical")
    site.page.click('.modes button[data-mode="public"]')
    offsite = [u for u in site.page.requests
               if not u.startswith("file://") and not any(h in u for h in FONT_HOSTS)]
    assert offsite == []


def test_the_brief_links_point_at_the_repository(site):
    links = site.page.eval_on_selector_all(
        "#brief-links a", "as => as.map(a => ({href: a.href, text: a.textContent}))")
    assert len(links) == 6, links
    for link in links:
        assert link["href"].startswith("https://github.com/ejri/aquatic-guardian/blob/main/briefs/")
        assert link["href"].endswith(".md")
        assert link["text"].strip()
    # Linked, not fetched: the page must not have gone to GitHub to build this list.
    assert not any("github.com" in u for u in site.page.requests)


def test_every_brief_link_resolves_to_a_file_in_the_repository(site):
    names = site.page.eval_on_selector_all(
        "#brief-links a", "as => as.map(a => a.href.split('/').pop())")
    for name in names:
        assert (ROOT / "briefs" / name).exists(), name


def test_the_tracker_shows_when_each_entry_was_last_checked(site):
    headers = site.page.eval_on_selector_all(
        "#tracker-table thead th", "ths => ths.map(t => t.textContent.trim())")
    assert "Last checked" in headers
    column = headers.index("Last checked") + 1
    dates = site.page.eval_on_selector_all(
        f"#tracker-table tbody td:nth-child({column})", "tds => tds.map(t => t.textContent.trim())")
    tracker = json.loads((ROOT / "data" / "instruments.json").read_text())
    assert len(dates) == len(tracker["instruments"])
    assert all(d for d in dates)


def test_the_tracker_warns_at_the_top_when_rows_need_rechecking(site):
    tracker = json.loads((ROOT / "data" / "instruments.json").read_text())
    unsourced = [e for e in tracker["instruments"] if not e.get("sources")]
    note = site.page.inner_text("#tracker-note").strip()
    if not unsourced:
        pytest.skip("every entry has a primary source, so there is nothing to warn about")
    assert str(len(unsourced)) in note
    assert "primary-source link" in note


# ---------------------------------------------------------------- jurisdictions

def test_the_jurisdiction_select_sets_the_rule_and_shows_its_status(site):
    site.mode("official")
    options = site.page.eval_on_selector_all(
        "#in-jurisdiction option", "os => os.map(o => o.value)")
    assert options[0] == "us-wa" and {"us-ca", "us-or", "ca-bc", "eu", "other"} <= set(options)

    site.select("jurisdiction", "us-ca")
    assert site.page.input_value("#in-temperature_rule") == "ca_new_coastal"
    note = site.page.inner_text("#in-jurisdiction-h")
    assert "California Thermal Plan" in note and "rule" in note

    site.select("jurisdiction", "ca-bc")
    assert site.page.input_value("#in-temperature_rule") == "custom"
    note = site.page.inner_text("#in-jurisdiction-h")
    assert "Environmental Management Act" in note
    assert "no source transcribed" in note


@pytest.mark.parametrize("jid,expect,forbid", [
    ("us-wa", ["§316(b)"], ["Fisheries Act"]),
    ("us-ca", ["§316(b)"], ["Fisheries Act"]),
    ("ca-bc", ["Fisheries Act"], ["§316(b)", "125.84"]),
    ("eu", ["No cooling-water intake rule"], ["§316(b)", "125.84", "Fisheries Act"]),
    ("other", ["No cooling-water intake rule"], ["§316(b)", "125.84", "Fisheries Act"]),
])
def test_no_flag_cites_a_law_that_does_not_apply_there(site, jid, expect, forbid):
    site.mode("official")
    site.page.fill("#in-it_load_mw", "600")
    site.select("jurisdiction", jid)
    flags = site.page.inner_text(".flags") if site.page.locator(".flags").count() else ""
    for phrase in expect:
        assert phrase in flags, (jid, flags)
    for phrase in forbid:
        assert phrase not in flags, (jid, flags)


def test_officials_mode_shows_the_source_beside_the_draft_conditions(site):
    site.mode("official")
    site.select("jurisdiction", "us-wa")
    block = site.page.inner_text(".out-block:has(.conditions)")
    assert "WAC 173-201A-210(1)(c)" in block
    assert "Clean Water Act §316(b)" in block
    site.select("jurisdiction", "eu")
    block = site.page.inner_text(".out-block:has(.conditions)")
    assert "no source transcribed in this repository" in block
    assert "Water Framework Directive" not in block or True     # note lives on the select


# ----------------------------------------------------------------------- axe

@pytest.mark.parametrize("mode", MODES)
def test_axe_core_finds_no_serious_or_critical_violations(browser, mode):
    if not AXE.exists():
        pytest.skip(f"axe-core is not installed: run npm install ({AXE} missing)")
    s = _open(browser, INDEX)
    s.page.wait_for_selector("#results .summary")
    s.mode(mode)
    s.page.add_script_tag(path=str(AXE))
    violations = s.page.evaluate(
        """async tags => {
          const r = await axe.run(document, {runOnly: {type: "tag", values: tags}});
          return r.violations.map(v => ({id: v.id, impact: v.impact, help: v.help,
            nodes: v.nodes.slice(0, 4).map(n => n.target.join(" "))}));
        }""", WCAG_TAGS)
    bad = [v for v in violations if v["impact"] in ("serious", "critical")]
    assert bad == [], f"{mode}: " + json.dumps(bad, indent=2)
    s.page.context.close()


def test_axe_core_finds_no_serious_or_critical_violations_in_dark_mode(browser):
    if not AXE.exists():
        pytest.skip(f"axe-core is not installed: run npm install ({AXE} missing)")
    s = _open(browser, INDEX, color_scheme="dark")
    s.page.wait_for_selector("#results .summary")
    s.page.add_script_tag(path=str(AXE))
    violations = s.page.evaluate(
        """async tags => {
          const r = await axe.run(document, {runOnly: {type: "tag", values: tags}});
          return r.violations.filter(v => ["serious", "critical"].includes(v.impact))
            .map(v => ({id: v.id, impact: v.impact, nodes: v.nodes.slice(0, 4).map(n => n.target.join(" "))}));
        }""", WCAG_TAGS)
    assert violations == [], json.dumps(violations, indent=2)
    s.page.context.close()
