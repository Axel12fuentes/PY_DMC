import requests
import re
import os
import pdfplumber
import time
from base_scraper import BaseScraper
from playwright.sync_api import sync_playwright

class DatascienceScraper(BaseScraper):
    def __init__(self):
        super().__init__("Datascience.pe")
        self.base_url = "https://www.datascience.pe/lista-cursos"
        self.download_dir = "scrapers/downloads"
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def get_urls(self):
        return [self.base_url]

    def parse_course(self, url):
        pass

    def parse_catalog(self):
        print(f"Starting Playwright scraper for: {self.base_url}")
        
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                # 1. Count Total Cards first
                print("Navigating to catalog to count cards...")
                page.goto(self.base_url, timeout=60000)
                try:
                    page.wait_for_load_state("networkidle", timeout=30000)
                except:
                    pass
                
                card_count = page.locator("a.card-link").count()
                print(f"Found {card_count} cards.")
                
                scraped_urls = set()

                # 2. Iterate by Index
                for i in range(card_count):
                    try:
                        print(f"Processing Card {i+1}/{card_count}...")
                        # Navigate fresh to catalog for each item to avoid stale handles/state
                        page.goto(self.base_url, timeout=60000)
                        page.wait_for_load_state("networkidle")
                        
                        # Re-locate the card
                        card = page.locator("a.card-link").nth(i)
                        
                        # Extract Overview Data (Prices, Title from List)
                        # Title (Sibling)
                        title = "Unknown"
                        # We need to traverse DOM relative to this card element
                        # locator doesn't support 'parent' easily without xpath or evaluate
                        # Use evaluate to get title from sibling
                        title = card.evaluate("""el => {
                            const parent = el.parentElement;
                            const titleEl = parent.querySelector('.card-title');
                            return titleEl ? titleEl.innerText : 'Unknown';
                        }""").strip()
                        if not title or title == "Unknown":
                             # Fallback text inside card
                             title = card.inner_text().split('\n')[0].strip()

                        # Prices
                        price_original = "N/A"
                        price_current = "N/A"
                        
                        # Use evaluate for robust extraction inside the element
                        prices = card.evaluate("""el => {
                            const p = { original: "N/A", current: "N/A" };
                            
                            // Old Price
                            const promoPro = el.querySelector('.card-promotion p');
                            if (promoPro) p.original = promoPro.innerText;
                            
                            // Current Price (Iterate all strongs in card-button)
                            const strongs = el.querySelectorAll('.card-button strong');
                            for (const s of strongs) {
                                if (s.innerText.includes('S/')) {
                                    p.current = s.innerText;
                                    break;
                                }
                            }
                            return p;
                        }""")
                        
                        if prices.get('original') and "Antes" in prices['original']:
                            price_original = prices['original'].replace("Antes", "").strip()
                        if prices.get('current') and "S/" in prices['current']:
                            price_current = prices['current'].strip()
                        
                        print(f"  Card Info: {title} | Cur: {price_current} | Orig: {price_original}")
                        
                        # Click to Navigate
                        card.click()
                        page.wait_for_load_state("networkidle")
                        
                        # Now we are on Detail Page
                        current_url = page.url
                        scraped_urls.add(current_url)
                        
                        # Scrape Detail Page
                        self.scrape_detail_page(page, current_url, title, price_current, price_original)
                        
                    except Exception as e:
                        print(f"Error processing card {i}: {e}")

                # 3. Handle Explicit URLs (if missed)
                explicit_urls = [
                    "https://www.datascience.pe/detalle/especializacion/data-analyst-IA"
                ]
                for e_url in explicit_urls:
                    if e_url not in scraped_urls:
                        print(f"Scraping explicit URL: {e_url}")
                        try:
                            page.goto(e_url, timeout=60000)
                            page.wait_for_load_state("networkidle")
                            # We don't have list prices for this if it wasn't on the list
                            self.scrape_detail_page(page, e_url, "Explicit: Data Analyst IA", "N/A", "N/A")
                        except Exception as e:
                            print(f"Error scraping explicit URL: {e}")

            except Exception as e:
                print(f"Error in parse_catalog: {e}")
            finally:
                browser.close()

    def scrape_detail_page(self, page, url, title, price_current, price_original):
        # Extract info from detail page
        data = page.evaluate("""() => {
            const result = {
                duration: "N/A",
                start_date: "N/A",
                brochure_url: "N/A"
            };
            
            // Brochure
            const brochureLinks = Array.from(document.querySelectorAll('a'))
                .filter(a => (a.href.includes('drive.google.com') || a.innerText.toLowerCase().includes('brochure')));
            
            if (brochureLinks.length > 0) {
                result.brochure_url = brochureLinks[0].href;
            }

            // Schedule details
            const details = document.querySelectorAll('.schedule-columns__details');
            details.forEach(det => {
                const txt = det.innerText;
                if (txt.includes('Inicio')) {
                    const p = det.querySelector('p');
                    result.start_date = p ? p.innerText : txt;
                }
                if (txt.includes('HRS') || txt.includes('Horas')) {
                        const p = det.querySelector('p');
                        result.duration = p ? p.innerText : txt;
                }
            });

            return result;
        }""")

        # Fallback duration
        if data['duration'] == 'N/A':
            body_text = page.inner_text('body')
            dur_match = re.search(r'(\d+\s*HRS\s*ACAD[ÉE]MICAS)', body_text, re.IGNORECASE)
            if dur_match:
                data['duration'] = dur_match.group(1)

        # PDF Extraction
        pdf_info = {}
        if "drive.google.com" in data['brochure_url']:
            pdf_path = self.download_brochure(data['brochure_url'], title)
            if pdf_path:
                pdf_info = self.extract_brochure_info(pdf_path)
        
        final_start_date = data['start_date'] if data['start_date'] != "N/A" else pdf_info.get("start_date", "N/A")
        final_duration = data['duration'] if data['duration'] != "N/A" else pdf_info.get("duration", "N/A")

        item = {
            "course_name": title,
            "course_type": "Specialization" if "especializacion" in url else "Course",
            "price_raw": price_current,
            "price_currency": "PEN",
            "price_original": price_original,
            "duration": final_duration,
            "url": url,
            "start_date": final_start_date,
            "brochure_url": data['brochure_url'],
            "content_updated": pdf_info.get("content", "N/A"),
            "instructor_exp": pdf_info.get("instructor", "N/A"),
            "methodology": pdf_info.get("methodology", "N/A"),
            "certification": pdf_info.get("certification", "N/A")
        }
        self.add_item(item)
        print(f"    Saved Item: {title}")

    def download_brochure(self, drive_url, course_name):
        file_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', drive_url)
        if not file_id_match:
            return None
        
        file_id = file_id_match.group(1)
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', course_name).strip('_')
        file_path = os.path.join(self.download_dir, f"{safe_name}.pdf")

        if os.path.exists(file_path):
            return file_path

        print(f"    Downloading brochure...")
        try:
            session = requests.Session()
            response = session.get(download_url, stream=True)
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    params = {'id': file_id, 'confirm': value}
                    response = session.get(download_url, params=params, stream=True)
                    break
            
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(32768):
                        if chunk:
                            f.write(chunk)
                return file_path
            return None
        except Exception as e:
            print(f"    Download error: {e}")
            return None

    def extract_brochure_info(self, pdf_path):
        from utils.llm_helper import LLMHelper
        if not hasattr(self, 'llm_helper'):
            self.llm_helper = LLMHelper()
        
        return self.llm_helper.extract_from_pdf(pdf_path)

if __name__ == "__main__":
    scraper = DatascienceScraper()
    scraper.parse_catalog()
    scraper.save_data()
