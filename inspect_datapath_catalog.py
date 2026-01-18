from playwright.sync_api import sync_playwright

url = "https://datapath.ai/cursos" # Guessing URL
# or https://cursos.datapath.ai/

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        # Try main site first
        print("Checking https://datapath.ai/cursos ...")
        page.goto("https://datapath.ai/cursos", timeout=60000)
        page.wait_for_load_state("networkidle")
        
        # Look for links to courses
        # Filter for links containing "bootcamp" or "curso"
        links = page.query_selector_all("a")
        print(f"Found {len(links)} total links.")
        
        course_links = set()
        for link in links:
            href = link.get_attribute("href")
            if href and ("/cursos/" in href or "bootcamp-" in href):
                if href.startswith("/"):
                    href = "https://datapath.ai" + href
                course_links.add(href)
        
        print(f"Possible course links: {list(course_links)}")
        
        # Try subdomain if main fails or yields few
        print("\nChecking https://cursos.datapath.ai/ ...")
        page.goto("https://cursos.datapath.ai/", timeout=60000)
        page.wait_for_load_state("networkidle")
        
        links = page.query_selector_all("a")
        for link in links:
            href = link.get_attribute("href")
            if href and ("/cursos/" in href or "bootcamp" in href):
                if href.startswith("/"):
                    href = "https://cursos.datapath.ai" + href
                course_links.add(href)
                
        print(f"Combined Unique Course Links: {len(course_links)}")
        for l in course_links:
            print(f" - {l}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        browser.close()
