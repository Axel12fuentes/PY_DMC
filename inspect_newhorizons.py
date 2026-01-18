from playwright.sync_api import sync_playwright

urls = [
    "https://www.newhorizons.edu.pe/",
    "https://www.newhorizons.edu.pe/cursos-y-certificaciones-internacionales/cloud/az-204t00-a-developing-solutions-for-microsoft-azure"
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 1. Check home/catalog
    print("=== Checking Home Page ===")
    page.goto(urls[0], timeout=60000)
    page.wait_for_load_state("networkidle")
    
    print(f"Title: {page.title()}")
    
    # Find course links
    links = page.query_selector_all("a")
    course_links = set()
    
    for link in links:
        href = link.get_attribute("href")
        if href and ("/cursos" in href or "/certificaciones" in href or "/curso/" in href):
            if "newhorizons.edu.pe" in href or href.startswith("/"):
                if href.startswith("/"):
                    href = "https://www.newhorizons.edu.pe" + href
                course_links.add(href)
    
    print(f"Found {len(course_links)} potential course links")
    for link in list(course_links)[:10]:
        print(f"  - {link}")
    
    # 2. Check detail page
    print("\n=== Checking Detail Page ===")
    page.goto(urls[1], timeout=60000)
    page.wait_for_load_state("networkidle")
    
    # Check for brochure button
    brochure_btns = page.get_by_text("brochure", exact=False).all()
    print(f"Found {len(brochure_btns)} 'brochure' buttons/links")
    
    download_btns = page.get_by_text("descargar", exact=False).all()
    print(f"Found {len(download_btns)} 'descargar' buttons/links")
    
    # Check for price
    price_text = page.get_by_text("S/", exact=False).all()
    print(f"Found {len(price_text)} elements with 'S/'")
    
    browser.close()
