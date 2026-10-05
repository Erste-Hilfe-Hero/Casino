# Copyright 2026 Andrei Vorobiev and Virtual Casino Simulator contributors
# SPDX-License-Identifier: Apache-2.0
"""BR-NOIRVA-ART-001: inspect every game route and original artwork in Chromium.

Uses isolated temporary simulator data. Checks all catalog games in EN/RU at the
four governed viewports, verifies decorative assets load, and exercises an actual
Eclipse spin. This presentation check does not replace each game's action suite.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import shutil
import subprocess
import tempfile
import time
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
VIEWPORTS = [("desktop_primary", 1920, 1080), ("desktop_compact", 1440, 900), ("tablet", 1024, 900), ("mobile", 390, 844)]
ARTIFACTS = {"cherry", "lemon", "bar", "bell", "seven", "wild", "scatter"}


def run(output):
    """Start an isolated local server and return durable after-pass evidence."""
    output.mkdir(parents=True, exist_ok=True)
    games = sorted((json.loads(path.read_text())["game"] for path in (ROOT / "modules").glob("*.json") if '"game":' in path.read_text()), key=lambda game: game["sort_order"])
    report = {"test_id": "BR-NOIRVA-ART-001", "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "rows": [], "failures": []}
    with tempfile.TemporaryDirectory(prefix="noirva-artwork-") as temporary:
        env = dict(os.environ, CASINO_DATA_DIR=temporary + "/data", CASINO_LOG_DIR=temporary + "/logs")
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        with (output / "server.log").open("w") as log:
            server = subprocess.Popen(["python", "run.py", "--host", "127.0.0.1", "--port", str(port), "--no-browser"], cwd=ROOT, env=env, stdout=log, stderr=log)
            try:
                for _ in range(100):
                    try:
                        urllib.request.urlopen(base, timeout=1).close()
                        break
                    except OSError:
                        time.sleep(.1)
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(executable_path=shutil.which("chromium") or playwright.chromium.executable_path, headless=True, args=["--no-sandbox"])
                    page = browser.new_page(viewport={"width": 1440, "height": 900})
                    errors = []
                    asset_failures = []
                    page.on("response", lambda response: asset_failures.append(response.url) if "/assets/noirva/" in response.url and response.status >= 400 else None)
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(base)
                    page.get_by_test_id("login-email").fill("admin@example.local")
                    page.get_by_test_id("login-password").fill("admin-password")
                    if page.get_by_test_id("login-terms-check").is_visible():
                        page.get_by_test_id("login-terms-check").check()
                    page.get_by_test_id("login-submit").click()
                    page.get_by_test_id("lobby").wait_for(timeout=15000)
                    if page.locator(".whats-new-dialog[open]").count():
                        page.locator(".whats-new-dialog[open] button").last.click()
                    for locale in ["en-US", "ru-RU"]:
                        page.get_by_test_id("shell-menu").evaluate("element => element.open = true")
                        page.locator("#shell-locale-select").select_option(locale)
                        page.get_by_test_id("shell-menu").evaluate("element => element.open = false")
                        for viewport, width, height in VIEWPORTS:
                            page.set_viewport_size({"width": width, "height": height})
                            for game in [None] + games:
                                game_id = game["id"] if game else "lobby"
                                row = {"surface": game_id if game else "shell_lobby", "state": "ready", "locale": locale, "viewport": viewport}
                                try:
                                    page.goto(base + (game["route"] if game else "/"), wait_until="domcontentloaded")
                                    page.get_by_test_id(game["frontend"]["ready_testid"] if game else "lobby").wait_for(timeout=15000)
                                    page.evaluate("async () => await Promise.all([...document.images].filter(image => image.src.includes('/assets/noirva/') && image.getBoundingClientRect().top < innerHeight).map(image => image.decode().catch(() => null)))")
                                    page.wait_for_timeout(100)
                                    geometry = page.evaluate("""() => ({
                                      overflow: document.documentElement.scrollWidth - innerWidth,
                                      brand: document.documentElement.dataset.brand,
                                      missing: [...document.images].filter(image => image.src.includes('/assets/noirva/') && image.complete && !image.naturalWidth).map(image => image.src),
                                      scene: getComputedStyle(document.body).backgroundImage
                                    })""")
                                    assert geometry["overflow"] <= 1, geometry
                                    assert geometry["brand"] == "noirva", geometry
                                    assert not geometry["missing"], geometry
                                    assert "cathedral.webp" in geometry["scene"], geometry
                                    row["geometry"] = geometry
                                    if game_id == "lobby":
                                        assert page.locator(".noirva-game-art").count() == 46
                                        families = page.locator(".noirva-game-art").evaluate_all("images => [...new Set(images.map(image => image.getAttribute('src').split('/').pop()))]")
                                        assert len(families) == 8, families
                                    if game_id == "slots":
                                        assert page.locator(".slot-grid .slots-symbol-icon").count() == 15
                                        faces = page.locator(".slot-grid .slots-symbol-icon").evaluate_all("elements => elements.map(element => element.getAttribute('src'))")
                                        assert all(Path(face).stem in ARTIFACTS for face in faces), faces
                                        for identity in ["slots-lines", "slots-line-bet", "slots-speed", "slots-spin"]:
                                            box = page.get_by_test_id(identity).bounding_box()
                                            assert box and box["x"] >= 0 and box["x"] + box["width"] <= width + 1, (identity, box)
                                        window = page.locator(".slots-reel-window").bounding_box()
                                        footer = page.locator(".slots-cabinet-footer").bounding_box()
                                        assert window["y"] + window["height"] <= footer["y"] + 1, (window, footer)
                                        # The settled view and actual spin keep artifact artwork, route and wallet.
                                        if viewport == "desktop_primary":
                                            page.get_by_test_id("slots-speed").select_option("fast")
                                            page.get_by_test_id("slots-spin").click()
                                            page.wait_for_function("() => document.querySelector('[data-testid=slots-premium]').dataset.motionPhase === 'settled' && !document.querySelector('[data-testid=slots-spin]').disabled", timeout=20000)
                                            assert "/games/slots" in page.url
                                            assert page.locator(".slot-grid .slots-symbol-icon").count() == 15
                                            page.emulate_media(reduced_motion="reduce")
                                            page.get_by_test_id("slots-spin").click()
                                            page.wait_for_function("() => document.querySelector('[data-testid=slots-premium]').dataset.motionPhase === 'settled' && !document.querySelector('[data-testid=slots-spin]').disabled", timeout=20000)
                                            assert page.locator(".slot-grid .slots-symbol-icon").count() == 15
                                            page.emulate_media(reduced_motion="no-preference")
                                            page.get_by_test_id("game-options-toggle").click()
                                            assert page.locator(".slots-drawer").is_visible()
                                            assert page.locator(".slots-paytable, [data-testid=slots-feature-summary]").first.is_visible()
                                            page.get_by_test_id("game-options-toggle").click()
                                            assert not page.locator(".slots-drawer").is_visible()
                                            row["state"] = "settled_after_normal_and_reduced_spin"
                                    if game_id in {"lobby", "slots", "blackjack", "roulette"}:
                                        path = f"{game_id}-{locale}-{viewport}.png"
                                        page.screenshot(path=str(output / path), full_page=True)
                                        row["evidence"] = path
                                    row["result"] = "PASS"
                                except Exception as failure:
                                    row["result"] = "FAIL"
                                    row["failure"] = str(failure)
                                    report["failures"].append(row.copy())
                                    print("FAIL", locale, viewport, game_id, str(failure)[:220], flush=True)
                                report["rows"].append(row)
                            print(locale, viewport, "checked", len(games), "games", flush=True)
                    if asset_failures:
                        report["failures"].append({"asset_http_failures": asset_failures})
                    if errors:
                        report["failures"].append({"page_errors": errors})
                    browser.close()
            finally:
                server.terminate()
                server.wait(timeout=10)
    report["result"] = "FAIL" if report["failures"] else "PASS"
    (output / "checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(report["result"], len(report["rows"]), "route / locale / viewport checks", flush=True)
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT.parent / "scratch" / "noirva-fantasy")
    raise SystemExit(run(parser.parse_args().output))
