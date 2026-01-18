from playwright.sync_api import sync_playwright

url = "https://smartdata.com.pe/cursos/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        print(f"Navigating to {url}...")
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        
        # Check title
        print(f"Page Title: {page.title()}")
        
        # Inspect headings
        h2s = page.query_selector_all("h2")
        print(f"Found {len(h2s)} h2 elements.")
        for h2 in h2s[:5]:
             print(f"H2: {h2.inner_text()}")
             
        # Inspect links
        links = page.query_selector_all("a")
        print(f"Found {len(links)} total links.")
        
        course_links = set()
        for link in links:
            href = link.get_attribute("href")
            if href and ("/curso/" in href or "/especializacion/" in href):
                 course_links.add(href)
        
        print(f"Filtered Course Links: {len(course_links)}")
        for l in list(course_links)[:5]:
             print(f" - {l}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        browser.close()
