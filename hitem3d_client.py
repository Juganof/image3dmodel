from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from pathlib import Path
import logging
import re
import subprocess
import time


def _ensure_browser_deps(logger: logging.Logger) -> None:
    """Best-effort install of Playwright browser binaries and system deps."""
    cmd = ["playwright", "install", "--with-deps", "chromium"]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as exc:
        logger.warning("[hitem3d] %s failed: %s", " ".join(cmd), exc)
        raise RuntimeError(
            "Playwright system dependencies are missing and automatic installation failed."
        ) from exc

def process_image_with_hitem3d(image_path: str, out_dir: str, prefer_formats=None, wait_minutes: int = 20, headless: bool = True):
    """
    Automates hitem3d.ai:
    - loads site
    - uploads image
    - waits for generation
    - downloads available formats into out_dir
    Returns list of downloaded file paths.
    """
    logger = logging.getLogger(__name__)
    prefer_formats = prefer_formats or ["glb","obj","stl"]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    downloaded_paths = []

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=headless)
        except Exception as exc:
            if "missing dependencies" in str(exc).lower():
                logger.info("[hitem3d] Installing Playwright browser dependencies ...")
                try:
                    _ensure_browser_deps(logger)
                except Exception:
                    raise RuntimeError(
                        "Playwright browser dependencies could not be installed."
                        " Install them manually with 'playwright install-deps'."
                    )
                browser = p.chromium.launch(headless=headless)
            else:
                raise
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(60_000)  # 60s default per action

        logger.info("[hitem3d] Opening site ...")
        page.goto("https://hitem3d.ai/", wait_until="domcontentloaded")

        # Try to find a file input; site is dynamic, so wait a bit and query common selectors.
        logger.info("[hitem3d] Looking for upload control ...")
        file_input = None
        candidate_selectors = [
            'input[type="file"]',
            'input[type="file"][accept]',
        ]
        for sel in candidate_selectors:
            try:
                file_input = page.locator(sel).first
                file_input.wait_for(state="attached", timeout=30_000)
                break
            except PlaywrightTimeoutError:
                pass

        if not file_input:
            raise RuntimeError("Unable to locate file input on hitem3d.ai. Try --headful to inspect selectors.")

        logger.info("[hitem3d] Uploading %s ...", image_path)
        file_input.set_input_files(image_path)

        # Wait for generation & links
        deadline = time.time() + (wait_minutes * 60)
        # Match any of the preferred extensions when scanning the page for
        # downloadable links. Previously this was hard-coded to GLB/OBJ/STL,
        # which meant supplying a different list via ``prefer_formats`` would
        # have no effect. Build the pattern dynamically so callers can extend
        # or override the formats.
        pat = re.compile(
            r"\.(?:" + "|".join([re.escape(ext) for ext in prefer_formats]) + r")$",
            re.I,
        )

        def find_href_links():
            anchors = page.eval_on_selector_all("a", "els => els.map(e => ({href: e.href, text: e.innerText}))")
            return [a for a in anchors if a.get("href") and pat.search(a["href"] or "")]

        logger.info("[hitem3d] Waiting for generation & download links ...")
        found_any = False
        while time.time() < deadline:
            page.wait_for_timeout(2000)
            links = find_href_links()
            if links:
                found_any = True
                break

        if not found_any:
            logger.warning("[hitem3d] No download links appeared before timeout.")
            return downloaded_paths

        # Try to click preferred formats in order.
        tried = set()
        for ext in prefer_formats:
            ext = ext.lower().strip()
            if not ext or ext in tried:
                continue
            tried.add(ext)

            # Click anchors whose href ends with that ext
            try:
                anchors = page.eval_on_selector_all("a", "els => els.map(e => ({href: e.href, text: e.innerText}))")
                matching = [a for a in anchors if (a.get("href") or "").lower().endswith("." + ext)]
                if matching:
                    with page.expect_download() as d_info:
                        page.locator(f'a[href$=".{ext}"]').first.click()
                    download = d_info.value
                    save_path = str((Path(out_dir) / f"model.{ext}").resolve())
                    download.save_as(save_path)
                    downloaded_paths.append(save_path)
                    logger.info("[hitem3d] Downloaded %s → %s", ext.upper(), save_path)
            except Exception as e:
                logger.warning("[hitem3d] Download %s failed: %s", ext, e)

        context.close()
        browser.close()

    return downloaded_paths
