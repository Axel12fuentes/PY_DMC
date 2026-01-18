import requests
import re
import os
import pdfplumber
import time
from base_scraper import BaseScraper
from playwright.sync_api import sync_playwright
from utils.llm_helper import LLMHelper

class DMCScraper(BaseScraper):
    def __init__(self):
        super().__init__("DMC")
        self.base_url = "https://dmc.pe/cursos/"
        self.download_dir = "scrapers/downloads/dmc"
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        self.llm_helper = LLMHelper()

    def get_urls(self):
        return [self.base_url]

    def parse_course(self, url):
        pass

    def parse_catalog(self):
        print(f"Starting Playwright scraper for DMC...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 1. Navigate to Catalog
            print(f"Navigating to: {self.base_url}")
            page.goto(self.base_url, timeout=60000)
            page.wait_for_load_state("networkidle")
            
            # 2. Extract Course Links
            # From previous inspection, items are in .brxe-div.brx-grid > div
            # But the links are the reliable part.
            links = page.query_selector_all("a")
            course_urls = set()
            for link in links:
                href = link.get_attribute("href")
                if href and ("/producto/" in href or "/curso/" in href or "/especializacion/" in href):
                    course_urls.add(href)
            
            print(f"Found {len(course_urls)} potential courses.")

            # 3. Iterate
            for url in course_urls:
                self.process_course_detail(page, url)
            
            browser.close()

    def process_course_detail(self, page, url):
        print(f"  Scraping: {url}")
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state('networkidle')
            
            # Title (h1)
            title = page.title()
            h1 = page.query_selector("h1")
            if h1: title = h1.inner_text().strip()

            # Price
            price_current = "N/A"
            price_original = "N/A"
            # DMC often uses WooCommerce structure
            # del for old, ins for new
            
            price_el = page.query_selector(".woocommerce-Price-amount")
            if price_el:
                # Try to get specific woocommerce elements
                # Current Price
                ins_el = page.query_selector("ins .woocommerce-Price-amount")
                if ins_el:
                    price_current = ins_el.inner_text().strip()
                else:
                    # Maybe just a single price
                    price_current = price_el.inner_text().strip()
                
                # Old Price
                del_el = page.query_selector("del .woocommerce-Price-amount")
                if del_el:
                    price_original = del_el.inner_text().strip()

            print(f"    Prices: {price_current} / {price_original}")

            # Brochure Download
            pdf_path = None
            brochure_url = "N/A"
            
            # Look for Brochure button
            # Button often opens a modal/popup id="popup-..."
            btn = page.get_by_text("Brochure", exact=False).first
            
            if btn.is_visible():
                print("    Found Brochure button. Attempting download...")
                btn.click()
                time.sleep(2) # Wait for modal
                
                # Check for form inputs
                # Inputs often have name='form_fields[...]' or just names
                # Inspector showed: s / Py ?? strange inputs names from previous run
                # Let's try filling standard field types if visible
                
                try:
                    # Fill standard fields if they exist
                    # Name
                    name_input = page.locator("input[type='text']").first
                    if name_input.is_visible(): name_input.fill("Juan Perez")

                    # Email
                    email_input = page.locator("input[type='email']").first
                    if email_input.is_visible(): email_input.fill("juan.perez.test@example.com")
                    
                    # Submit
                    # Wait for download triggers
                    with page.expect_download(timeout=15000) as download_info:
                         # Click submit
                        submit = page.locator("button[type='submit']").first
                        if submit.is_visible():
                            submit.click()
                        else:
                            # Try generic button inside form
                            form_btn = page.locator("form button").first
                            if form_btn.is_visible(): form_btn.click()
                    
                    download = download_info.value
                    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', title).strip('_') + ".pdf"
                    pdf_path = os.path.join(self.download_dir, safe_name)
                    download.save_as(pdf_path)
                    print(f"    Downloaded: {pdf_path}")
                    brochure_url = "Downloaded via Form"

                except Exception as e:
                    # Sometimes brochure is just a link without form
                    print(f"    Brochure form/download failed: {e}")
                    # Try direct link search?
                    # pdf_link = page.query_selector("a[href$='.pdf']")
            
            # PDF Extraction
            pdf_info = {}
            if pdf_path and os.path.exists(pdf_path):
                 pdf_info = self.llm_helper.extract_from_pdf(pdf_path)

            item = {
                "course_name": title,
                "course_type": "Especialización" if "especializacion" in url else "Curso",
                "price_raw": price_current,
                "price_currency": "PEN" if "S/" in price_current else "USD",
                "price_original": price_original,
                "duration": pdf_info.get("duration", "N/A"),
                "url": url,
                "start_date": pdf_info.get("start_date", "N/A"),
                "brochure_url": brochure_url,
                "content_updated": pdf_info.get("content", "N/A"),
                "instructor_exp": pdf_info.get("instructor", "N/A"),
                "methodology": pdf_info.get("methodology", "N/A"),
                "certification": pdf_info.get("certification", "N/A")
            }
            self.add_item(item)
            
        except Exception as e:
            print(f"  Error processing {url}: {e}")

if __name__ == "__main__":
    scraper = DMCScraper()
    scraper.parse_catalog()
    scraper.save_data()
