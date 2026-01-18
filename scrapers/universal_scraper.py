import os
import time
import re
from base_scraper import BaseScraper
from playwright.sync_api import sync_playwright
from utils.llm_helper import LLMHelper

class UniversalScraper(BaseScraper):
    """
    Scraper universal que usa LLM para extraer información del HTML.
    Mucho más robusto que selectores específicos.
    """
    def __init__(self, site_name, catalog_url, download_dir_name):
        super().__init__(site_name)
        self.catalog_url = catalog_url
        self.download_dir = f"scrapers/downloads/{download_dir_name}"
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        self.llm_helper = LLMHelper()

    def get_urls(self):
        return [self.catalog_url]

    def parse_course(self, url):
        pass

    def parse_catalog(self):
        print(f"Starting LLM-powered scraper for {self.source_name}...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 1. Navegar al catálogo
            print(f"Navigating to catalog: {self.catalog_url}")
            page.goto(self.catalog_url, timeout=60000)
            page.wait_for_load_state("networkidle")
            
            # 2. Encontrar todos los enlaces de cursos
            # (Esto aún requiere un patrón básico, pero es más flexible)
            links = page.query_selector_all("a")
            course_urls = set()
            
            # Patrones comunes para identificar cursos
            course_patterns = [
                "/curso/", "/cursos/", "/especializacion/", "/producto/", 
                "/bootcamp", "/diploma", "/course/",
                "/cursos-y-certificaciones-internacionales/"  # New Horizons
            ]
            
            # Palabras a excluir
            exclude_patterns = ["login", "category", "filtro", "cart", "ver-todas", 
                              "gad_source", "utm_", "search"]
            
            for link in links:
                href = link.get_attribute("href")
                if href and any(pattern in href.lower() for pattern in course_patterns):
                    # Filtrar links administrativos usando exclude_patterns
                    if not any(skip in href.lower() for skip in exclude_patterns):
                        if href.startswith("/"):
                            # Construir URL absoluta
                            from urllib.parse import urljoin
                            href = urljoin(self.catalog_url, href)
                        course_urls.add(href)
            
            print(f"Found {len(course_urls)} potential courses.")

            # 3. Scrape cada curso
            for url in course_urls:
                self.process_course_detail(page, url)
            
            browser.close()

    def process_course_detail(self, page, url):
        print(f"  Scraping: {url}")
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state('networkidle')
            
            # === PASO 1: Extraer info básica con LLM ===
            html_content = page.content()
            llm_data = self.llm_helper.extract_from_html(html_content, url)
            
            print(f"    LLM extracted: {llm_data.get('course_name')} | {llm_data.get('price_raw')}")

            # === PASO 2: Descargar brochure si existe ===
            pdf_path = None
            brochure_url = "N/A"
            
            # Buscar botones de brochure (patrones comunes)
            brochure_keywords = ["brochure", "descargar", "plan de estudios", "temario"]
            btn = None
            
            for keyword in brochure_keywords:
                btn = page.get_by_text(keyword, exact=False).first
                if btn.is_visible():
                    print(f"    Found button: '{keyword}'")
                    break
            
            if btn and btn.is_visible():
                pdf_path = self.attempt_brochure_download(page, btn, llm_data.get("course_name", "course"))
                if pdf_path:
                    brochure_url = "Downloaded via Form"

            # === PASO 3: Extraer info adicional del PDF ===
            pdf_info = {}
            if pdf_path and os.path.exists(pdf_path):
                pdf_info = self.llm_helper.extract_from_pdf(pdf_path)
                print(f"    PDF extracted: {pdf_info.get('duration')} | {pdf_info.get('certification')}")

            # === PASO 4: Combinar datos ===
            # Prioridad: LLM HTML > PDF > N/A
            item = {
                "course_name": llm_data.get("course_name", "N/A"),
                "course_type": llm_data.get("course_type", "Curso"),
                "price_raw": llm_data.get("price_raw", "N/A"),
                "price_currency": self.detect_currency(llm_data.get("price_raw", "")),
                "price_original": llm_data.get("price_original", "N/A"),
                "duration": llm_data.get("duration") if llm_data.get("duration") != "N/A" else pdf_info.get("duration", "N/A"),
                "start_date": llm_data.get("start_date") if llm_data.get("start_date") != "N/A" else pdf_info.get("start_date", "N/A"),
                "instructor": llm_data.get("instructor") if llm_data.get("instructor") != "N/A" else pdf_info.get("instructor", "N/A"),
                "modality": llm_data.get("modality", "N/A"),
                "url": url,
                "brochure_url": brochure_url,
                "certification": pdf_info.get("certification", "N/A"),
                "methodology": pdf_info.get("methodology", "N/A"),
                "content": pdf_info.get("content", "N/A")
            }
            self.add_item(item)
            
        except Exception as e:
            print(f"  Error processing {url}: {e}")

    def attempt_brochure_download(self, page, btn, course_name):
        """Intenta descargar el brochure haciendo clic en el botón."""
        try:
            with page.expect_download(timeout=20000) as download_info:
                btn.click()
                time.sleep(1)
                
                # Buscar y llenar formularios si aparecen
                if page.locator("input[type='text'], input[type='email']").first.is_visible(timeout=2000):
                    # Llenar campos comunes
                    for field in page.locator("input[type='text']").all():
                        if field.is_visible():
                            field.fill("Juan Perez", timeout=1000)
                            break
                    
                    for field in page.locator("input[type='email']").all():
                        if field.is_visible():
                            field.fill("test@example.com", timeout=1000)
                            break
                    
                    # Checkboxes
                    for checkbox in page.locator("input[type='checkbox']").all():
                        if checkbox.is_visible():
                            try:
                                checkbox.check(force=True, timeout=1000)
                            except:
                                pass
                    
                    # Submit
                    time.sleep(1)
                    for submit in page.locator("button[type='submit'], input[type='submit']").all():
                        if submit.is_visible():
                            submit.click(timeout=2000)
                            break
            
            download = download_info.value
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', course_name).strip('_')[:50] + ".pdf"
            pdf_path = os.path.join(self.download_dir, safe_name)
            download.save_as(pdf_path)
            print(f"    Downloaded: {safe_name}")
            return pdf_path
            
        except Exception as e:
            print(f"    Brochure download skipped: {e}")
            return None

    def detect_currency(self, price_str):
        """Detecta la moneda del string de precio."""
        if "S/" in price_str or "PEN" in price_str:
            return "PEN"
        elif "$" in price_str or "USD" in price_str:
            return "USD"
        elif "€" in price_str or "EUR" in price_str:
            return "EUR"
        return "N/A"

# Ejemplo de uso
if __name__ == "__main__":
    # Scraper para Datapath
    scraper = UniversalScraper(
        site_name="Datapath.ai",
        catalog_url="https://cursos.datapath.ai/",
        download_dir_name="datapath_v2"
    )
    scraper.parse_catalog()
    scraper.save_data()
