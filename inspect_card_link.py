from playwright.sync_api import sync_playwright

url = "https://www.datascience.pe/lista-cursos"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)
    try:
        page.wait_for_load_state("networkidle")
        
        cards = page.query_selector_all("a.card-link")
        print(f"Found {len(cards)} card links.")
        
        for i, card in enumerate(cards[:3]):
            print(f"--- Card {i} ---")
            print(f"Href: {card.get_attribute('href')}")
            print(f"Outer HTML: {card.evaluate('el => el.outerHTML')[:300]}")
            
            # Check Sibling .card-title
            parent = card.evaluate_handle("el => el.parentElement") # .card-properties
            title_div = parent.query_selector(".card-title")
            if title_div:
                print(f"Title Div HTML: {title_div.evaluate('el => el.outerHTML')[:300]}")
                # Check for link inside title
                link = title_div.query_selector("a")
                if link:
                    print(f"Link inside Title: {link.get_attribute('href')}")
            else:
                print("No title div found.")

    except Exception as e:
        print(e)
    finally:
        browser.close()
