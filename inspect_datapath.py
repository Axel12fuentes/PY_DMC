from playwright.sync_api import sync_playwright
import time

url = "https://cursos.datapath.ai/cursos/bootcamp-data-engineer"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        print(f"Navigating to {url}...")
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        
        # Look for "Descargar Brochure" button
        # It's likely a button that opens a modal or a form directly on page
        buttons = page.get_by_text("Descargar Brochure", exact=False).all()
        print(f"Found {len(buttons)} 'Descargar Brochure' buttons.")
        
        # Click the button
        print("Clicking 'Descargar Brochure'...")
        buttons[0].click()
        time.sleep(2) # Wait for animation
        
        print("\n=== Inspecting Visible Form Inputs ===")
        inputs = page.query_selector_all("input")
        for inp in inputs:
            if inp.is_visible():
                print(f"VISIBLE Input: name='{inp.get_attribute('name')}', type='{inp.get_attribute('type')}'")
        
        # Check for submit button
        submits = page.query_selector_all("button[type='submit'], input[type='submit']")
        print(f"Found {len(submits)} submit buttons.")
        for s in submits:
            if s.is_visible():
                print(f"VISIBLE Submit: {s.inner_text()}")

        print("\n=== Inspecting Price Context ===")
        # Look for elements containing "$"
        price_els = page.get_by_text("$").all()
        for i, el in enumerate(price_els):
            # Print parent text to see context (e.g. "$480")
            parent = el.locator("xpath=..")
            print(f"Price {i} Parent Text: {parent.inner_text()}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        browser.close()
