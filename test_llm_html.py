"""
Prueba de extracción basada en LLM para una página de curso.
Esto demuestra cómo el LLM puede leer el HTML directamente.
"""
from playwright.sync_api import sync_playwright
from utils.llm_helper import LLMHelper

url = "https://cursos.datapath.ai/cursos/bootcamp-data-engineer"

print(f"Testing LLM-based HTML extraction on: {url}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(url, timeout=60000)
    page.wait_for_load_state("networkidle")
    
    # Get the full HTML
    html_content = page.content()
    
    # Use LLM to extract
    helper = LLMHelper()
    result = helper.extract_from_html(html_content, url)
    
    print("\n=== LLM Extraction Results ===")
    for key, value in result.items():
        print(f"{key}: {value}")
    
    browser.close()
