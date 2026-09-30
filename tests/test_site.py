"""Browser checks for the published audience site, driven with Playwright (Chromium).

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

sync_api = pytest.importorskip(
    "playwright.sync_api",
    reason='playwright is not installed: pip install -e ".[site]"',
)

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "site" / "index.html"
NOT_FOUND = ROOT / "site" / "404.html"
AXE = ROOT / "node_modules" / "axe-core" / "axe.min.js"
FONT_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")
WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
DESKTOP = {"width": 1366, "height": 900}
PHONE = {"width": 390, "height": 844}
# Hash routes for the four audiences (plus home for smoke).
ROUTES = ["public", "officials", "lab", "industry"]


class Site:
    """A loaded page plus the console errors it produced."""

    def __init__(self, page, errors):
        self.page, self.errors = page, errors

    @property
    def unexpected_errors(self) -> list[str]:
        """Console errors other than the deliberately blocked Google Fonts requests."""
        return [e for e in self.errors if not any(h in e for h in FONT_HOSTS)]

    def go(self, route: str) -> None:
        self.page.evaluate(f"location.hash = '#/{route}'")
        self.page.wait_for_selector(f'[data-route="{route}"].on', timeout=60_000)
        # Audience tools mount on first visit; wait a beat for screening output.
        if route in ("officials", "industry"):
            tool = "official" if route == "officials" else "technical"
            self.page.wait_for_selector(f'[data-tool="{tool}"] .res-summary, [data-tool="{tool}"] .err', timeout=60_000)

    def tool_select(self, field: str, value: str, tool: str = "official") -> None:
        sel = f'[data-tool="{tool}"] [data-k="{field}"]'
        self.page.select_option(sel, value)
        self.page.wait_for_selector(f'[data-tool="{tool}"] .res-summary')

    def tool_fill(self, field: str, value: str, tool: str = "official") -> None:
        sel = f'[data-tool="{tool}"] [data-k="{field}"]'
        self.page.fill(sel, value)
        self.page.wait_for_selector(f'[data-tool="{tool}"] .res-summary')


@pytest.fixture(scope="session")
def browser():
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as exc:  # noqa: BLE001 - the message is the point
            pytest.skip(
                f"Chromium is not installed: python -m playwright install chromium ({exc})"
            )
        yield b
        b.close()


def _open(browser, url: Path, **context_kwargs) -> Site:
    ctx = browser.new_context(**{"viewport": DESKTOP, **context_kwargs})
    page = ctx.new_page()
    errors: list[str] = []
    page.requests = []
    page.on("request", lambda r: page.requests.append(r.url))
    page.on(
        "console",
        lambda m: errors.append(f"{m.location.get('url', '')} {m.text}")
        if m.type == "error"
        else None,
    )
    page.on("pageerror", lambda e: errors.append(f"pageerror {e}"))
    page.route(f"**/*{{{','.join(FONT_HOSTS)}}}/**", lambda route: route.abort())
    for host in FONT_HOSTS:
        page.route(f"https://{host}/**", lambda route: route.abort())
    page.goto(url.as_uri())
    # Audience index activates a route; the 404 page has no data-route panels.
    if page.locator("[data-route]").count():
        page.wait_for_selector('[data-route="home"].on, [data-route].on', timeout=60_000)
    else:
        page.wait_for_selector("main h1", timeout=60_000)
    return Site(page, errors)


@pytest.fixture
def site(browser):
    s = _open(browser, INDEX)
    yield s
    s.page.context.close()


def test_the_page_loads_with_no_console_errors(site):
    assert site.unexpected_errors == []
    assert site.page.title().startswith("Aquatic Guardian")


def test_404_page_loads_cleanly_and_links_home(browser):
    s = _open(browser, NOT_FOUND)
    assert s.unexpected_errors == []
    assert "not found" in s.page.title().lower()
    assert s.page.locator('main a[href="/"], main a[href="#/"]').count() >= 1
    assert s.page.locator("h1").count() == 1
    s.page.context.close()


@pytest.mark.parametrize("route", ROUTES)
def test_no_horizontal_scroll_on_a_390px_phone(browser, route):
    s = _open(browser, INDEX, viewport=PHONE)
    s.go(route)
    overflow = s.page.evaluate(
        "() => ({doc: document.documentElement.scrollWidth, win: window.innerWidth})"
    )
    assert overflow["doc"] <= overflow["win"] + 1, (route, overflow)
    assert s.unexpected_errors == []
    s.page.context.close()


@pytest.mark.parametrize("route", ROUTES)
def test_every_input_has_a_label(site, route):
    site.go(route)
    unlabelled = site.page.evaluate(
        """(route) => {
      const root = document.querySelector('[data-route="' + route + '"].on')
        || document;
      const bad = [];
      for (const el of root.querySelectorAll("input, select, textarea")) {
        if (el.type === "hidden") continue;
        const byId = el.id && document.querySelector('label[for="' + el.id + '"]');
        const wrapped = el.closest("label");
        const aria = el.getAttribute("aria-label");
        const ref = el.getAttribute("aria-labelledby");
        const named = (byId && byId.textContent.trim())
          || (wrapped && wrapped.textContent.trim())
          || (aria && aria.trim())
          || (ref && document.getElementById(ref));
        if (!named) bad.push(el.outerHTML.slice(0, 120));
      }
      return bad;
    }""",
        route,
    )
    assert unlabelled == [], (route, unlabelled)


def test_officials_screening_tool_produces_results(site):
    site.go("officials")
    site.page.wait_for_selector('[data-tool="official"] .res-summary')
    text = site.page.inner_text('[data-tool="official"]')
    assert "heat to water" in text
    assert "MW" in text and "m³/s" in text
    assert "Screening only" in text
    assert "Draft permit conditions" in text
    assert "Aquatic Disclosure Record" in text


def test_industry_screening_tool_shows_technical_detail(site):
    site.go("industry")
    site.page.wait_for_selector('[data-tool="technical"] .res-summary')
    text = site.page.inner_text('[data-tool="technical"]')
    assert "Technical detail" in text
    assert "Aquatic Disclosure Record" in text


def test_public_cross_section_updates_with_facility_size(site):
    site.go("public")
    site.page.wait_for_selector("#xsec-text .big, #xsec-text")
    before = site.page.inner_text("#xsec-text")
    site.page.fill("#p-mw", "120")
    site.page.wait_for_function(
        "prev => document.querySelector('#xsec-text').textContent !== prev",
        arg=before,
    )
    after = site.page.inner_text("#xsec-text")
    assert after != before


def test_lab_route_shows_notebook_results_and_simulations(site):
    site.go("lab")
    assert site.page.locator("#sim-tide").count() == 1
    assert site.page.locator("#handoff-json").count() == 1
    site.page.wait_for_function(
        "() => (document.querySelector('#handoff-json') || {}).textContent.length > 40"
    )
    handoff = site.page.inner_text("#handoff-json")
    assert "plume" in handoff or "delta_t" in handoff
    assert site.page.locator("#ver-table tbody tr").count() >= 20


def test_model_language_tabs_move_with_arrow_keys(site):
    site.go("officials")
    tabs = site.page.locator("#jur button")
    assert tabs.count() >= 2
    first = tabs.nth(0)
    first.click()
    assert first.get_attribute("aria-selected") == "true"
    before = site.page.inner_text("#doc")
    site.page.keyboard.press("ArrowRight")
    assert tabs.nth(1).get_attribute("aria-selected") == "true"
    assert tabs.nth(0).get_attribute("aria-selected") == "false"
    assert site.page.inner_text("#doc") != before
    site.page.keyboard.press("ArrowLeft")
    assert tabs.nth(0).get_attribute("aria-selected") == "true"
    assert site.page.inner_text("#doc") == before


def test_dark_mode_renders_the_dark_tokens(browser):
    s = _open(browser, INDEX, color_scheme="dark")
    bg = s.page.evaluate("() => getComputedStyle(document.body).backgroundColor")
    # --bg dark token in web/parts/1_head.html is #051820
    assert bg == "rgb(5, 24, 32)", bg
    assert s.unexpected_errors == []
    s.page.context.close()


def test_the_page_requests_nothing_but_google_fonts(site):
    """The self-contained rule, checked rather than asserted in a comment."""
    for route in ROUTES:
        site.go(route)
    offsite = [
        u
        for u in site.page.requests
        if not u.startswith("file://") and not any(h in u for h in FONT_HOSTS)
    ]
    assert offsite == []


def test_the_brief_links_point_at_the_repository(site):
    site.go("lab")
    site.page.wait_for_selector("#brief-links a")
    links = site.page.eval_on_selector_all(
        "#brief-links a", "as => as.map(a => ({href: a.href, text: a.textContent}))"
    )
    assert len(links) == 6, links
    for link in links:
        assert link["href"].startswith(
            "https://github.com/ejri/aquatic-guardian/blob/main/briefs/"
        )
        assert link["href"].endswith(".md")
        assert link["text"].strip()
    assert not any("github.com" in u for u in site.page.requests)


def test_every_brief_link_resolves_to_a_file_in_the_repository(site):
    site.go("lab")
    site.page.wait_for_selector("#brief-links a")
    names = site.page.eval_on_selector_all(
        "#brief-links a", "as => as.map(a => a.href.split('/').pop())"
    )
    for name in names:
        assert (ROOT / "briefs" / name).exists(), name


def test_the_tracker_shows_when_each_entry_was_last_checked(site):
    site.go("officials")
    site.page.wait_for_selector("#tracker tbody tr")
    headers = site.page.eval_on_selector_all(
        "#tracker thead th", "ths => ths.map(t => t.textContent.trim())"
    )
    assert "Last checked" in headers
    column = headers.index("Last checked") + 1
    dates = site.page.eval_on_selector_all(
        f"#tracker tbody td:nth-child({column})",
        "tds => tds.map(t => t.textContent.trim())",
    )
    tracker = json.loads((ROOT / "data" / "instruments.json").read_text())
    assert len(dates) == len(tracker["instruments"])
    assert all(d for d in dates)


def test_the_tracker_warns_at_the_top_when_rows_need_rechecking(site):
    site.go("officials")
    site.page.wait_for_selector("#tracker-note")
    tracker = json.loads((ROOT / "data" / "instruments.json").read_text())
    unsourced = [e for e in tracker["instruments"] if not e.get("sources")]
    note = site.page.inner_text("#tracker-note").strip()
    if not unsourced:
        pytest.skip("every entry has a primary source, so there is nothing to warn about")
    assert str(len(unsourced)) in note
    assert "primary-source" in note


# ---------------------------------------------------------------- jurisdictions


def test_the_jurisdiction_select_sets_the_rule_and_shows_its_status(site):
    site.go("officials")
    site.page.wait_for_selector('[data-tool="official"] [data-k="jurisdiction"]')
    options = site.page.eval_on_selector_all(
        '[data-tool="official"] [data-k="jurisdiction"] option',
        "os => os.map(o => o.value)",
    )
    assert options[0] == "us-wa" and {"us-ca", "us-or", "ca-bc", "eu", "other"} <= set(
        options
    )

    site.tool_select("jurisdiction", "us-ca")
    assert (
        site.page.input_value('[data-tool="official"] [data-k="temperature_rule"]')
        == "ca_new_coastal"
    )
    note = site.page.inner_text(
        '[data-tool="official"] [data-k="jurisdiction"] ~ small, '
        '[data-tool="official"] small[id$="-jurisdiction-h"]'
    )
    # help text is sibling small with id ending -jurisdiction-h
    note = site.page.evaluate(
        """() => {
          const sel = document.querySelector('[data-tool="official"] [data-k="jurisdiction"]');
          const h = sel && document.getElementById(sel.getAttribute('aria-describedby'));
          return h ? h.textContent : '';
        }"""
    )
    assert "California Thermal Plan" in note and "rule" in note

    site.tool_select("jurisdiction", "ca-bc")
    assert (
        site.page.input_value('[data-tool="official"] [data-k="temperature_rule"]')
        == "custom"
    )
    note = site.page.evaluate(
        """() => {
          const sel = document.querySelector('[data-tool="official"] [data-k="jurisdiction"]');
          const h = sel && document.getElementById(sel.getAttribute('aria-describedby'));
          return h ? h.textContent : '';
        }"""
    )
    assert "Environmental Management Act" in note
    assert "no source transcribed" in note


@pytest.mark.parametrize(
    "jid,expect,forbid",
    [
        ("us-wa", ["§316(b)"], ["Fisheries Act"]),
        ("us-ca", ["§316(b)"], ["Fisheries Act"]),
        ("ca-bc", ["Fisheries Act"], ["§316(b)", "125.84"]),
        ("eu", ["No cooling-water intake rule"], ["§316(b)", "125.84", "Fisheries Act"]),
        (
            "other",
            ["No cooling-water intake rule"],
            ["§316(b)", "125.84", "Fisheries Act"],
        ),
    ],
)
def test_no_flag_cites_a_law_that_does_not_apply_there(site, jid, expect, forbid):
    site.go("officials")
    site.page.wait_for_selector('[data-tool="official"] [data-k="jurisdiction"]')
    site.tool_fill("it_load_mw", "600")
    site.tool_select("jurisdiction", jid)
    flags = (
        site.page.inner_text('[data-tool="official"] .flags')
        if site.page.locator('[data-tool="official"] .flags').count()
        else ""
    )
    for phrase in expect:
        assert phrase in flags, (jid, flags)
    for phrase in forbid:
        assert phrase not in flags, (jid, flags)


def test_officials_mode_shows_the_source_beside_the_draft_conditions(site):
    site.go("officials")
    site.page.wait_for_selector('[data-tool="official"] .conditions')
    site.tool_select("jurisdiction", "us-wa")
    block = site.page.inner_text('[data-tool="official"]')
    assert "WAC 173-201A-210(1)(c)" in block
    assert "Clean Water Act" in block and "316(b)" in block
    site.tool_select("jurisdiction", "eu")
    block = site.page.inner_text('[data-tool="official"]')
    assert "no source transcribed" in block.lower() or "No cooling-water intake rule" in block


# ----------------------------------------------------------------------- axe


@pytest.mark.parametrize("route", ROUTES)
def test_axe_core_finds_no_serious_or_critical_violations(browser, route):
    if not AXE.exists():
        pytest.skip(f"axe-core is not installed: run npm install ({AXE} missing)")
    s = _open(browser, INDEX)
    s.go(route)
    s.page.add_script_tag(path=str(AXE))
    violations = s.page.evaluate(
        """async tags => {
          const r = await axe.run(document, {runOnly: {type: "tag", values: tags}});
          return r.violations.map(v => ({id: v.id, impact: v.impact, help: v.help,
            nodes: v.nodes.slice(0, 4).map(n => n.target.join(" "))}));
        }""",
        WCAG_TAGS,
    )
    bad = [v for v in violations if v["impact"] in ("serious", "critical")]
    assert bad == [], f"{route}: " + json.dumps(bad, indent=2)
    s.page.context.close()


def test_axe_core_finds_no_serious_or_critical_violations_in_dark_mode(browser):
    if not AXE.exists():
        pytest.skip(f"axe-core is not installed: run npm install ({AXE} missing)")
    s = _open(browser, INDEX, color_scheme="dark")
    s.go("officials")
    s.page.add_script_tag(path=str(AXE))
    violations = s.page.evaluate(
        """async tags => {
          const r = await axe.run(document, {runOnly: {type: "tag", values: tags}});
          return r.violations.filter(v => ["serious", "critical"].includes(v.impact))
            .map(v => ({id: v.id, impact: v.impact, nodes: v.nodes.slice(0, 4).map(n => n.target.join(" "))}));
        }""",
        WCAG_TAGS,
    )
    assert violations == [], json.dumps(violations, indent=2)
    s.page.context.close()
