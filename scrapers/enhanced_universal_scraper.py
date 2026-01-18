"""
Scraper Universal Mejorado v2 - Usa GPT-4o para descubrimiento de catálogo
Máxima robustez sin restricciones de costo
"""
import os
import time
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseScraper
from playwright.sync_api import sync_playwright
from utils.llm_helper import LLMHelper

class EnhancedUniversalScraper(BaseScraper):
    """
    Versión mejorada con GPT-4o para máxima extracción.
    """
    def __init__(self, site_name, catalog_url, download_dir_name, max_pagination=10, max_courses=None):
        super().__init__(site_name)
        self.catalog_url = catalog_url
        self.download_dir = f"scrapers/downloads/{download_dir_name}"
        self.max_pagination = max_pagination  # Límite de páginas a scrapear
        self.max_courses = max_courses  # Límite de cursos (None = todos)
        
        # Timeouts específicos por sitio (algunos necesitan más tiempo)
        slow_sites = ["bsg", "we_educacion", "upc", "platzi"]
        self.page_timeout = 120000 if download_dir_name in slow_sites else 90000  # 120s vs 90s
        self.networkidle_timeout = 90000 if download_dir_name in slow_sites else 60000  # 90s vs 60s
        
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        self.llm_helper = LLMHelper()

    def get_urls(self):
        return [self.catalog_url]

    def parse_course(self, url):
        pass

    def parse_catalog(self):
        print(f"🚀 Starting ENHANCED LLM scraper for {self.source_name}...")
        print(f"   Using GPT-4o for intelligent catalog discovery")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            all_course_urls = set()
            visited_pages = set()
            pages_to_visit = [self.catalog_url]
            pagination_count = 0
            
            # === FASE 1: Descubrimiento inteligente de TODOS los cursos ===
            while pages_to_visit and pagination_count < self.max_pagination:
                current_url = pages_to_visit.pop(0)
                
                if current_url in visited_pages:
                    continue
                    
                print(f"\n📑 Analizando catálogo página {pagination_count + 1}: {current_url[:80]}...")
                visited_pages.add(current_url)
                pagination_count += 1
                
                try:
                    page.goto(current_url, timeout=self.page_timeout)
                    page.wait_for_load_state("networkidle", timeout=self.networkidle_timeout)
                    
                    # Scroll para cargar contenido lazy-load
                    for i in range(3):
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(1)
                    
                    # === MÉTODO PRINCIPAL: Pattern-Based (más confiable) ===
                    found_urls = self.llm_helper.discover_course_links_pattern_fallback(page)
                    print(f"   ✅ Patrones encontraron {len(found_urls)} cursos")
                    
                    # === PAGINACIÓN: Buscar siguiente página ===
                    next_page = None
                    
                    # Método 1: Buscar botón "Siguiente" o "Next"
                    next_keywords = ["siguiente", "next", "›", "→", ">"]
                    for keyword in next_keywords:
                        next_btn = page.get_by_text(keyword, exact=False).all()
                        for btn in next_btn:
                            if btn.is_visible():
                                href = btn.get_attribute("href")
                                if href:
                                    if href.startswith("/"):
                                        from urllib.parse import urljoin
                                        href = urljoin(current_url, href)
                                    next_page = href
                                    break
                        if next_page:
                            break
                    
                    # Método 2: Buscar en los links de paginación
                    if not next_page:
                        pagination_links = page.query_selector_all("a.page-link, a.pagination, nav a")
                        for link in pagination_links:
                            text = link.inner_text().strip() if link.is_visible() else ""
                            href = link.get_attribute("href")
                            if text and href:
                                # Si es un número mayor al actual
                                if text.isdigit():
                                    # Buscar número en URL actual
                                    import re
                                    current_page_match = re.search(r'/page/(\d+)', current_url)
                                    if current_page_match:
                                        current_page_num = int(current_page_match.group(1))
                                        if int(text) == current_page_num + 1:
                                            if href.startswith("/"):
                                                from urllib.parse import urljoin
                                                href = urljoin(current_url, href)
                                            next_page = href
                                            break
                    
                    # Normalizar URLs encontradas
                    for url in found_urls:
                        if url.startswith("/"):
                            from urllib.parse import urljoin
                            url = urljoin(current_url, url)
                        all_course_urls.add(url)
                    
                    # Agregar siguiente página si existe
                    if next_page and next_page not in visited_pages:
                        if next_page.startswith("/"):
                            from urllib.parse import urljoin
                            next_page = urljoin(current_url, next_page)
                        pages_to_visit.append(next_page)
                        print(f"   🔗 Siguiente página detectada: {next_page[:80]}")
                        
                except Exception as e:
                    print(f"   ⚠️  Error en página: {e}")
            
            print(f"\n📊 TOTAL de cursos únicos encontrados: {len(all_course_urls)}")
            
            # === FASE 2: Extracción de datos de cada curso ===
            # Limitar si es modo prueba
            courses_to_scrape = list(all_course_urls)
            if self.max_courses:
                courses_to_scrape = courses_to_scrape[:self.max_courses]
                print(f"🧪 MODO PRUEBA: Limitando a {self.max_courses} cursos")
            
            for idx, url in enumerate(courses_to_scrape, 1):
                print(f"\n[{idx}/{len(courses_to_scrape)}] ", end="")
                self.process_course_detail(page, url)
            
            browser.close()
            
        print(f"\n✅ Scraping completo: {len(self.data)} cursos extraídos")

    def process_course_detail(self, page, url):
        print(f"Scraping: {url[:80]}...")
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state('networkidle', timeout=20000)
            
            # Extracción con LLM
            html_content = page.content()
            llm_data = self.llm_helper.extract_from_html(html_content, url)
            
            course_name = llm_data.get("course_name", "N/A")
            print(f"    ✓ {course_name}")

            # Intentar descargar brochure
            pdf_path = None
            brochure_url = "N/A"
            
            brochure_keywords = [
                "brochure", "descargar", "plan de estudios", "temario", 
                "syllabus", "download", "pdf", "malla"
            ]
            
            btn = None
            for keyword in brochure_keywords:
                matches = page.get_by_text(keyword, exact=False).all()
                for match in matches:
                    if match.is_visible():
                        btn = match
                        break
                if btn:
                    break
            
            if btn and btn.is_visible():
                pdf_path = self.attempt_brochure_download(page, btn, course_name)
                if pdf_path:
                    brochure_url = "Downloaded via Form"

            # Extracción PDF
            pdf_info = {}
            if pdf_path and os.path.exists(pdf_path):
                pdf_info = self.llm_helper.extract_from_pdf(pdf_path)

            # Combinar datos
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
            print(f"    ❌ Error: {e}")

    def attempt_brochure_download(self, page, btn, course_name):
        """Intenta descargar brochure de forma robusta."""
        try:
            with page.expect_download(timeout=15000) as download_info:
                btn.click()
                time.sleep(1)
                
                # Llenar formularios si aparecen
                if page.locator("input[type='text'], input[type='email']").first.is_visible(timeout=2000):
                    for field in page.locator("input[type='text']").all():
                        if field.is_visible():
                            field.fill("Juan Perez", timeout=1000)
                            break
                    
                    for field in page.locator("input[type='email']").all():
                        if field.is_visible():
                            field.fill("test@example.com", timeout=1000)
                            break
                    
                    for checkbox in page.locator("input[type='checkbox']").all():
                        if checkbox.is_visible():
                            try:
                                checkbox.check(force=True, timeout=1000)
                            except:
                                pass
                    
                    time.sleep(1)
                    for submit in page.locator("button[type='submit'], input[type='submit']").all():
                        if submit.is_visible():
                            submit.click(timeout=2000)
                            break
            
            download = download_info.value
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', course_name).strip('_')[:50] + ".pdf"
            pdf_path = os.path.join(self.download_dir, safe_name)
            download.save_as(pdf_path)
            return pdf_path
            
        except Exception as e:
            return None

    def detect_currency(self, price_str):
        """Detecta moneda del precio."""
        if "S/" in price_str or "PEN" in price_str:
            return "PEN"
        elif "$" in price_str or "USD" in price_str:
            return "USD"
        elif "€" in price_str or "EUR" in price_str:
            return "EUR"
        return "N/A"
