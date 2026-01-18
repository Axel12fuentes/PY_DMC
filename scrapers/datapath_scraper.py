import requests
import re
import os
import pdfplumber
import time
from base_scraper import BaseScraper
from playwright.sync_api import sync_playwright

class DatapathScraper(BaseScraper):
    def __init__(self):
        super().__init__("Datapath.ai")
        # Ensure we have at least one starting point. We can search for more later.
        self.base_url = "https://cursos.datapath.ai/cursos/bootcamp-data-engineer"
        self.download_dir = "scrapers/downloads/datapath"
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def get_urls(self):
        return [self.base_url]

    def parse_course(self, url):
        pass

    def parse_catalog(self):
        print(f"Starting Playwright scraper for Datapath catalog...")
        
        from playwright.sync_api import sync_playwright
        from utils.llm_helper import LLMHelper
        
        self.llm_helper = LLMHelper()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 1. Crawl Catalog to find links
            catalog_url = "https://cursos.datapath.ai/"
            print(f"Navigating to catalog: {catalog_url}")
            page.goto(catalog_url, timeout=60000)
            page.wait_for_load_state("networkidle")
            
            links = page.query_selector_all("a")
            course_urls = set()
            for link in links:
                href = link.get_attribute("href")
                # Filter for course links. Usually /cursos/ or /courses/
                if href and ("/cursos/" in href or "bootcamp" in href) and "login" not in href:
                    if href.startswith("/"):
                        href = "https://cursos.datapath.ai" + href
                    course_urls.add(href)
            
            print(f"Found {len(course_urls)} potential course URLs: {course_urls}")

            # 2. Iterate and Scrape
            for url in course_urls:
                self.process_course_detail(page, url)
            
            browser.close()

    def process_course_detail(self, page, url):
        print(f"  Scraping: {url}")
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state('networkidle')
            
            # Extract Title
            title = page.title()
            h1 = page.query_selector("h1")
            if h1: title = h1.inner_text().strip()

            # Extract Prices
            price_current = "N/A"
            price_original = "N/A"
            
            # Helper to clean price text
            def clean_price(txt):
                match = re.search(r'(\d+)', txt)
                return int(match.group(1)) if match else 0

            price_els = page.get_by_text("$").all()
            prices_found = []
            for el in price_els:
                parent = el.locator("xpath=..")
                txt = parent.inner_text().replace('\n', '').strip()
                val = clean_price(txt)
                if val > 0:
                    prices_found.append(val)
            
            prices_found = sorted(list(set(prices_found)))
            if len(prices_found) > 0:
                price_current = f"${prices_found[0]}" 
            if len(prices_found) > 1:
                price_original = f"${prices_found[-1]}"

            print(f"    Prices: {price_current} / {price_original}")

            # Brochure Download
            pdf_path = None
            brochure_url = "N/A"
            
            # Look for button - exact=False to match "Descargar Brochure" or "Brochure"
            btn = page.get_by_text("Descargar Brochure", exact=False).first
            if not btn.is_visible():
                 btn = page.get_by_text("Brochure", exact=False).first

            if btn.is_visible():
                print("    Found Brochure button. Initiating download flow...")
                
                try:
                    with page.expect_download(timeout=30000) as download_info:
                        btn.click()
                        time.sleep(1)
                        
                        # Form Filling
                        if page.locator("input[name='Nombre']").is_visible():
                            page.fill("input[name='Nombre']", "Juan")
                            page.fill("input[name='Apellido']", "Perez")
                            page.fill("input[name='Correo']", "juan.perez.test@example.com")
                            page.fill("input[name='phone']", "999999999")
                            
                            # Checkbox
                            checkbox = page.locator("input[name='Checkbox']")
                            if checkbox.is_visible(timeout=2000):
                                try:
                                    checkbox.check(force=True)
                                except:
                                    page.evaluate("document.querySelector(\"input[name='Checkbox']\").click()")
                            
                            time.sleep(1)
                            submit_btn = page.locator("input[type='submit']")
                            if submit_btn.is_visible():
                                submit_btn.click()
                            else:
                                page.locator("button[type='submit']").click()
                    
                    download = download_info.value
                    # Clean filename
                    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', title).strip('_') + ".pdf"
                    pdf_path = os.path.join(self.download_dir, safe_name)
                    download.save_as(pdf_path)
                    print(f"    Downloaded: {pdf_path}")
                    brochure_url = "Downloaded via Form"
                except Exception as e:
                    print(f"    Download skipped or failed: {e}")
            else:
                print("    No Brochure button found.")

            # PDF Extraction using LLMHelper
            pdf_info = {}
            if pdf_path and os.path.exists(pdf_path) and hasattr(self, 'llm_helper'):
                pdf_info = self.llm_helper.extract_from_pdf(pdf_path)
            
            # Defaults
            start_date = pdf_info.get("start_date", "N/A")
            duration = pdf_info.get("duration", "N/A")

            item = {
                "course_name": title,
                "course_type": "Bootcamp" if "bootcamp" in url.lower() else "Course",
                "price_raw": price_current,
                "price_currency": "USD",
                "price_original": price_original,
                "duration": duration,
                "url": url,
                "start_date": start_date,
                "brochure_url": brochure_url,
                "content_updated": pdf_info.get("content", "N/A"),
                "instructor_exp": pdf_info.get("instructor", "N/A"),
                "methodology": pdf_info.get("methodology", "N/A"),
                "certification": pdf_info.get("certification", "N/A")
            }
            self.add_item(item)
            
        except Exception as e:
            print(f"  Error processing course {url}: {e}")

    # extract_brochure_info removed in favor of LLMHelper

if __name__ == "__main__":
    scraper = DatapathScraper()
    scraper.parse_catalog()
    scraper.save_data()
