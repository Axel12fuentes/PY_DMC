from playwright.sync_api import sync_playwright

url = "https://www.datascience.pe/lista-cursos"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        page.goto(url)
        # Wait for dynamic content
        page.wait_for_load_state("networkidle")
        
        promotions = page.get_by_text("Antes S/", exact=False).all()
        print(f"Found {len(promotions)} promo elements.")
        
        for i, promo in enumerate(promotions[:3]):
            print(f"--- Promo {i} ---")
            print(f"Text: {promo.inner_text()}")
            
            # Check ancestors
            parent = promo.locator("xpath=..")
            grandparent = promo.locator("xpath=../..")
            greatgrandparent = promo.locator("xpath=../../..")
            
            print(f"Parent Class: {parent.get_attribute('class')}")
            print(f"Parent HTML: {parent.evaluate('el => el.outerHTML')[:200]}")
            
            print(f"Grandparent Class: {grandparent.get_attribute('class')}")
            print(f"Grandparent HTML: {grandparent.evaluate('el => el.outerHTML')[:200]}")
            
            print(f"GreatGrandparent Class: {greatgrandparent.get_attribute('class')}")
            # Check if link is in grandparent
            links_gp = grandparent.locator("a[href*='/detalle/']").count()
            print(f"Links in Grandparent: {links_gp}")
            
            links_ggp = greatgrandparent.locator("a[href*='/detalle/']").count()
            print(f"Links in GreatGrandparent: {links_ggp}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        browser.close()
