import requests
import re
import os
import pdfplumber
import time
from base_scraper import BaseScraper
from playwright.sync_api import sync_playwright
from utils.llm_helper import LLMHelper

class SmartDataScraper(BaseScraper):
    def __init__(self):
        super().__init__("SmartData")
        self.base_url = "https://smartdata.com.pe/cursos/"
        self.download_dir = "scrapers/downloads/smartdata"
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        self.llm_helper = LLMHelper()

    def get_urls(self):
        return [self.base_url]

    def parse_course(self, url):
        pass

    def parse_catalog(self):
        print(f"Starting Playwright scraper for SmartData...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 1. Navigate to Catalog
            print(f"Navigating to: {self.base_url}")
            page.goto(self.base_url, timeout=60000)
            page.wait_for_load_state("networkidle")
            
            # 2. Extract Course Links
            # Use robust filtering as per inspection
            links = page.query_selector_all("a")
            course_urls = set()
            for link in links:
                href = link.get_attribute("href")
                if href and ("/curso/" in href or "/especializacion/" in href) and "course-category" not in href:
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
            
            # Title
            title = page.title()
            h1 = page.query_selector("h1.tutor-course-title")
            if h1: title = h1.inner_text().strip()

            # Price
            price_current = "N/A"
            price_original = "N/A"
            
            # SmartData usually has .price .amount
            # Or WooCommerce structure
            price_els = page.query_selector_all(".price .amount")
            # If multiple, assumption: first is current, second is old? or vice-versa?
            # Or look for del/ins
            
            ins_el = page.query_selector("ins .amount")
            del_el = page.query_selector("del .amount")
            
            if ins_el:
                price_current = ins_el.inner_text().strip()
            elif price_els:
                price_current = price_els[0].inner_text().strip()
                
            if del_el:
                price_original = del_el.inner_text().strip()

            print(f"    Prices: {price_current} / {price_original}")

            # Brochure Download
            pdf_path = None
            brochure_url = "N/A"
            
            # Look for button "Descargar plan de estudios" or "Brochure"
            # It might target a modal: #ums_course_brochure_modal
            btn = page.get_by_text("Descargar plan de estudios", exact=False).first
            if not btn.is_visible():
                btn = page.get_by_text("Brochure", exact=False).first
            
            if btn.is_visible():
                print("    Found Brochure button. Initiating form flow...")
                btn.click()
                time.sleep(2)
                
                # Check for form inputs
                # SmartData uses TutorLMS or similar.
                # Form might be in a modal.
                
                # Try simple form filling
                try:
                    name_in = page.locator("input[name*='name']").first
                    if name_in.is_visible(): name_in.fill("Juan Perez")
                    
                    email_in = page.locator("input[name*='email']").first
                    if email_in.is_visible(): email_in.fill("juan.perez.test@example.com")
                    
                    phone_in = page.locator("input[name*='phone']").first
                    if phone_in.is_visible(): phone_in.fill("999999999")

                    with page.expect_download(timeout=15000) as download_info:
                        submit = page.locator("button[type='submit']").first
                        if submit.is_visible():
                            submit.click()
                        else:
                            # Try finding submit input
                            page.locator("input[type='submit']").first.click()

                    download = download_info.value
                    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', title).strip('_') + ".pdf"
                    pdf_path = os.path.join(self.download_dir, safe_name)
                    download.save_as(pdf_path)
                    print(f"    Downloaded: {pdf_path}")
                    brochure_url = "Downloaded via Form"
                except Exception as e:
                    print(f"     Brochure download error: {e}")
            
            # PDF Extraction
            pdf_info = {}
            if pdf_path and os.path.exists(pdf_path):
                 pdf_info = self.llm_helper.extract_from_pdf(pdf_path)

            item = {
                "course_name": title,
                "course_type": "Especialización" if "especializacion" in url else "Curso",
                "price_raw": price_current,
                "price_currency": "PEN" if "S/" in price_current else "USD",
                "price_raw_original": price_original, # Keeping naming flexible
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
    scraper = SmartDataScraper()
    scraper.parse_catalog()
    scraper.save_data()
