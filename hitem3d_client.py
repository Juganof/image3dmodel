from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from pathlib import Path
import re
import time

def process_image_with_hitem3d(image_path: str, out_dir: str, prefer_formats=None, wait_minutes: int = 20, headless: bool = True):
    """
    Automates hitem3d.ai:
    - loads site
    - uploads image
    - waits for generation
    - downloads available formats into out_dir
    Returns list of downloaded file paths.
    """
    prefer_formats = prefer_formats or ["glb","obj","stl"]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    downloaded_paths = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(60_000)  # 60s default per action

        print("[hitem3d] Opening site ...")
        page.goto("https://hitem3d.ai/", wait_until="domcontentloaded")

        # Try to find a file input; site is dynamic, so wait a bit and query common selectors.
        print("[hitem3d] Looking for upload control ...")
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

        print(f"[hitem3d] Uploading {image_path} ...")
        file_input.set_input_files(image_path)

        # Wait for generation & links
        deadline = time.time() + (wait_minutes * 60)
        pat = re.compile(r'\.(?:' + "|".join([re.escape(ext) for ext in ["glb","obj","stl"]]) + r')$', re.I)

        def find_href_links():
            anchors = page.eval_on_selector_all("a", "els => els.map(e => ({href: e.href, text: e.innerText}))")
            return [a for a in anchors if a.get("href") and pat.search(a["href"] or "")]

        print("[hitem3d] Waiting for generation & download links ...")
        found_any = False
        while time.time() < deadline:
            page.wait_for_timeout(2000)
            links = find_href_links()
            if links:
                found_any = True
                break

        if not found_any:
            print("[hitem3d] No download links appeared before timeout.")
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
                    print(f"[hitem3d] Downloaded {ext.upper()} → {save_path}")
            except Exception as e:
                print(f"[hitem3d] Download {ext} failed: {e}")

        context.close()
        browser.close()

    return downloaded_paths
