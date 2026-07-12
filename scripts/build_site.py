#!/usr/bin/env python
"""Assemble a fully static version of the Council of Experts write-up for Netlify.

The live site (``server/``) is a FastAPI app: the Results page reads
``/api/prompts`` and ``/api/imported/{case_id}`` at runtime, and the A/B landing
page runs live deliberations against local Ollama models + the Claude API.

Netlify is static hosting, so this script:

1. Bakes the two read-only endpoints the Results page needs into committed JSON
   under ``site/data/`` (``prompts.json`` + ``imported/{case_id}.json``).
2. Copies the CSS / fonts / JS and the three static pages
   (Results, Process, Architecture) into ``site/``.
3. Patches ``results.js`` to fetch the baked JSON instead of the API.
4. Rewrites navigation so Results is the home page and the (backend-only)
   A/B runner is dropped everywhere.

Run from the repo root with the bench extra installed:

    uv run --extra bench python scripts/build_site.py

The output ``site/`` directory is self-contained — commit it and point Netlify's
publish directory at it (see ``netlify.toml``). No build step runs on Netlify.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "server" / "static"
SITE = ROOT / "site"

# The seven canonical cases the Results page tabs through (mirrors the CASES
# array in results.js). We bake one imported-runs file per case.
CASE_IDS = [
    "case_1_clinical_decision_support",
    "case_2_cross_border_digital_therapeutic",
    "case_3_capitated_risk_contract",
    "case_4_glp1_employer_coverage",
    "case_5_nonprofit_hospital_pe_conversion",
    "case_6_trigger_heavy_biotech_ma",
    "case_7_trigger_light_baseline",
]

# Pages carried over to the static site. index.html (the A/B runner) is dropped;
# the Results page becomes the home page instead.
STATIC_PAGES = ["results.html", "process.html", "architecture.html"]


def clean() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    (SITE / "data" / "imported").mkdir(parents=True)
    (SITE / "static" / "js").mkdir(parents=True)


def copy_assets() -> None:
    """Copy the self-hosted CSS, fonts, and JS under site/static/.

    The pages reference assets by absolute ``/static/...`` URLs (the live
    FastAPI app mounts them there), so we mirror that layout to keep every
    ``<link>`` / ``<script>`` / CSS ``url()`` reference working unchanged.

    Only ``results.js`` is carried over — ``app.js`` and ``disposition.js``
    belonged to the dropped A/B runner page and are loaded by nothing else.
    """
    shutil.copytree(STATIC / "css", SITE / "static" / "css")
    shutil.copytree(STATIC / "fonts", SITE / "static" / "fonts")
    shutil.copyfile(STATIC / "js" / "results.js", SITE / "static" / "js" / "results.js")


def bake_data() -> None:
    """Dump the two read-only API payloads the Results page consumes."""
    # Import lazily so the module docstring / --help works without deps.
    from server.app import get_imported_runs, get_prompts

    (SITE / "data" / "prompts.json").write_text(
        json.dumps(get_prompts(), indent=2, ensure_ascii=False), encoding="utf-8"
    )

    for case_id in CASE_IDS:
        payload = get_imported_runs(case_id)
        (SITE / "data" / "imported" / f"{case_id}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    print(f"  baked prompts.json + {len(CASE_IDS)} imported case files")


# ---------------------------------------------------------------------------
# JS patching — repoint the Results page fetches at the baked JSON.
# ---------------------------------------------------------------------------


def patch_js() -> None:
    results_js = SITE / "static" / "js" / "results.js"
    src = results_js.read_text(encoding="utf-8")

    before = src
    src = src.replace('fetch("/api/prompts")', 'fetch("/data/prompts.json")')
    src = src.replace(
        "fetch(`/api/imported/${encodeURIComponent(caseId)}`)",
        "fetch(`/data/imported/${encodeURIComponent(caseId)}.json`)",
    )
    if src == before:
        raise SystemExit("patch_js: expected fetch() call sites not found in results.js")
    results_js.write_text(src, encoding="utf-8")
    print("  patched results.js API fetches -> /data/*.json")


# ---------------------------------------------------------------------------
# HTML patching — nav + internal A/B links.
# ---------------------------------------------------------------------------

# The primary-nav block, rewritten so Results is home and A/B is gone. The
# `{results_active}` / `{process_active}` / `{architecture_active}` slots get
# the active class filled per page.
NAV_TEMPLATE = """      <nav class="primary-nav" aria-label="Primary">
        <a href="/"{results_active}>Results</a>
        <a href="/process"{process_active}>Process</a>
        <a href="/architecture"{architecture_active}>Architecture</a>
      </nav>"""

NAV_RE = re.compile(
    r'      <nav class="primary-nav" aria-label="Primary">.*?</nav>', re.DOTALL
)


def rewrite_nav(html: str, active: str) -> str:
    nav = NAV_TEMPLATE.format(
        results_active=' class="active"' if active == "results" else "",
        process_active=' class="active"' if active == "process" else "",
        architecture_active=' class="active"' if active == "architecture" else "",
    )
    new, n = NAV_RE.subn(nav, html)
    if n != 1:
        raise SystemExit(f"rewrite_nav: expected exactly 1 nav block, found {n}")
    return new


def strip_ab_links(html: str) -> str:
    """Neutralize inline body/footer links that pointed at the A/B page.

    The A/B runner no longer exists on the static site, so links like
    ``<a href="/">A/B page</a>`` are rewritten to plain text, and footer
    ``· <a href="/">A/B</a>`` fragments are dropped.
    """
    # Footer pattern: " · <a href="/">A/B</a>"  -> remove entirely.
    html = re.sub(r'\s*·\s*<a href="/">A/B</a>', "", html)
    # Inline "<a href="/">A/B page</a>" -> "A/B page" (plain text).
    html = re.sub(r'<a href="/">A/B page</a>', "the A/B page (local only)", html)
    # Any remaining bare "<a href="/">A/B</a>" -> plain text.
    html = re.sub(r'<a href="/">A/B</a>', "A/B", html)
    return html


def process_pages() -> None:
    # results.html doubles as the home page: emit it as both results.html and
    # index.html so "/" and "/results" both resolve without a redirect.
    for page in STATIC_PAGES:
        active = page.replace(".html", "")
        html = (STATIC / page).read_text(encoding="utf-8")
        html = rewrite_nav(html, active)
        html = strip_ab_links(html)
        (SITE / page).write_text(html, encoding="utf-8")

    shutil.copyfile(SITE / "results.html", SITE / "index.html")
    print(f"  wrote {len(STATIC_PAGES)} pages + index.html (Results as home)")


def main() -> None:
    print("Building static site -> site/")
    clean()
    copy_assets()
    bake_data()
    patch_js()
    process_pages()
    print("Done. Publish directory: site/")


if __name__ == "__main__":
    main()
