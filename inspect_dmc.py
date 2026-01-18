from playwright.sync_api import sync_playwright
import time

url = "https://dmc.pe/cursos/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        print(f"Navigating to {url}...")
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        
        # Check Catalog structure
        cards = page.query_selector_all(".brxe-div.brx-grid > div") # from old scraper
        if not cards:
             cards = page.query_selector_all("a.brxe-button") # Maybe buttons?
        print(f"Found {len(cards)} potential items in catalog.")
        
        # Pick one url to inspect detail
        detail_url = None
        # Try to find a link to a course
        links = page.query_selector_all("a")
        for link in links:
            href = link.get_attribute("href")
            if href and ("/producto/" in href or "/curso/" in href or "/especializacion/" in href):
                detail_url = href
                break
        
        if detail_url:
            print(f"Inspecting detail: {detail_url}")
            page.goto(detail_url, timeout=60000)
            page.wait_for_load_state("networkidle")
            
            # Look for Brochure button
            print("Checking for Brochure button...")
            btns = page.get_by_text("Brochure", exact=False).all()
            print(f"Found {len(btns)} brochure buttons.")
            
            # Inspect inputs if we clicked one (simulated)
            # Just print inputs on page for now
            inputs = page.query_selector_all("input")
            for inp in inputs:
                if inp.is_visible():
                     print(f"Input: {inp.get_attribute('name')} / {inp.get_attribute('placeholder')}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        browser.close()
