"""
Script masivo para inspeccionar múltiples sitios educativos.
Extrae info estructura, cantidad de cursos y requisitos especiales.
"""
from playwright.sync_api import sync_playwright
import time

sites = [
    {
        "name": "BSG Institute",
        "url": "https://bsginstitute.com/",
        "patterns": ["/curso", "/programa", "/especializacion", "/diplomado"]
    },
    {
        "name": "WE Educación",
        "url": "https://we-educacion.com/",
        "patterns": ["/curso", "/programa", "/especializacion"]
    },
    {
        "name": "PUCP InfoPUCP",
        "url": "https://infopucp.pucp.edu.pe/",
        "patterns": ["/curso", "/programa", "/especializacion"]
    },
    {
        "name": "PUCP Educación Continua",
        "url": "https://educacioncontinua.pucp.edu.pe/",
        "patterns": ["/curso", "/programa", "/diplomado"]
    },
    {
        "name": "UPC Postgrado",
        "url": "https://postgrado.upc.edu.pe/landings/programas-especializados/",
        "patterns": ["/programa", "/especializacion"]
    },
    {
        "name": "ED Team",
        "url": "https://ed.team/",
        "patterns": ["/curso", "/carrera", "/ruta"]
    },
    {
        "name": "Platzi",
        "url": "https://platzi.com/",
        "patterns": ["/curso", "/ruta", "/escuela"]
    }
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    for site in sites:
        print(f"\n{'='*60}")
        print(f"🔍 Analizando: {site['name']}")
        print(f"{'='*60}")
        
        try:
            page = browser.new_page()
            page.goto(site['url'], timeout=60000)
            page.wait_for_load_state("networkidle", timeout=30000)
            
            print(f"✅ Título: {page.title()}")
            
            # Detectar links de cursos
            links = page.query_selector_all("a")
            course_links = set()
            
            for link in links:
                href = link.get_attribute("href")
                if href:
                    for pattern in site['patterns']:
                        if pattern in href.lower():
                            if href.startswith("/"):
                                from urllib.parse import urljoin
                                href = urljoin(site['url'], href)
                            course_links.add(href)
            
            print(f"📚 Cursos encontrados: {len(course_links)}")
            
            # Muestra primeros 5
            for i, link in enumerate(list(course_links)[:5]):
                print(f"  {i+1}. {link}")
            
            # Detectar paginación
            pagination_keywords = ["siguiente", "next", "página", "page", "más", "ver más", "load more"]
            pagination_found = False
            for keyword in pagination_keywords:
                if page.get_by_text(keyword, exact=False).count() > 0:
                    pagination_found = True
                    print(f"⚠️  Posible paginación detectada: '{keyword}'")
                    break
            
            if not pagination_found:
                print("ℹ️  No se detectó paginación obvia")
            
            # Scroll infinito?
            initial_height = page.evaluate("document.body.scrollHeight")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            new_height = page.evaluate("document.body.scrollHeight")
            
            if new_height > initial_height:
                print("🔄 Scroll infinito detectado - contenido se carga dinámicamente")
            
            page.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if 'page' in locals():
                page.close()
    
    browser.close()

print(f"\n{'='*60}")
print("✅ Análisis completo")
print(f"{'='*60}")
