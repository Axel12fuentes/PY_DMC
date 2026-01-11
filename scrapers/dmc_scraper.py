import requests
from bs4 import BeautifulSoup
import re
from base_scraper import BaseScraper

class DMCScraper(BaseScraper):
    def __init__(self):
        super().__init__("DMC")
        self.base_url = "https://dmc.pe/cursos/?_filtro_categorias_productos=especializaciones%2Cdiplomas%2Ccursos"

    def get_urls(self):
        # In this specific case, we scrape from the catalog view directly as requested.
        # This method could be used to gather URLs for detail pages if needed later.
        return [self.base_url]

    def parse_course(self, url):
        # This is for a single course detail page. 
        # For now, let's implement the catalog parsing logic.
        pass

    def parse_catalog(self):
        print(f"Fetching catalog from: {self.base_url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(self.base_url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching catalog: {e}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Based on analysis, courses are in a grid.
        # Each course card seems to be represented by a block containing an image and info.
        # Let's look for the common container.
        course_cards = soup.select('.brxe-div.brx-grid > div')
        
        if not course_cards:
            # Fallback if the grid selector is too specific
            course_cards = soup.select('.dmc-borde-bottom')
            # If we select .dmc-borde-bottom, we are selecting the info part. 
            # We might need to go up or find the corresponding image part.
        
        print(f"Found {len(course_cards)} course cards potential matches.")

        for card in course_cards:
            try:
                # Title
                title_el = card.find('h3')
                if not title_el:
                    # Try finding in the whole card if it's a different structure
                    title_el = card.select_one('.brxe-heading')
                
                course_name = title_el.get_text(strip=True) if title_el else "N/A"
                if course_name == "N/A": continue # Skip if no title found

                # Type (Label in the corner)
                # Usually in a separate absolute positioned div/span
                type_el = card.find_previous_sibling() # This is tricky if we are iterating over children
                # Let's try to find it within the card's parent if it's split
                card_container = card.parent
                
                # Based on subagent, info part is .brxe-e29b7b and type is in .brxe-eea505
                # They might be siblings.
                course_type = "N/A"
                # Search for labels like "Cursos", "Diplomas", "Especializaciones"
                label_candidates = card.select('.brxe-text, .brxe-heading, span')
                for cand in label_candidates:
                    txt = cand.get_text(strip=True)
                    if txt in ["Cursos", "Diplomas", "Especializaciones", "Certificaciones"]:
                        course_type = txt
                        break

                # Prices
                price_normal = "N/A"
                price_offer = "N/A"
                price_currency = "PEN" # Default based on site observation (S/)

                # WooCommerce structure
                del_price = card.select_one('del .woocommerce-Price-amount')
                ins_price = card.select_one('ins .woocommerce-Price-amount')
                
                if del_price:
                    price_normal = del_price.get_text(strip=True)
                if ins_price:
                    price_offer = ins_price.get_text(strip=True)
                else:
                    # If no 'ins', maybe it's just a regular price
                    reg_price = card.select_one('.woocommerce-Price-amount')
                    if reg_price:
                        price_offer = reg_price.get_text(strip=True)

                # Duration and Start Date
                duration = "N/A"
                start_date = "N/A"
                
                text_blocks = card.get_text(separator='|').split('|')
                for block in text_blocks:
                    block = block.strip()
                    if "Sesiones" in block:
                        duration = block
                    if "Inicio:" in block:
                        start_date = block.replace("Inicio:", "").strip()

                # URL
                url_el = card.select_one('a.btn-clic, a.brxe-button')
                course_url = url_el['href'] if url_el and url_el.has_attr('href') else "N/A"
                if course_url == "N/A":
                    # Check if the title is a link
                    link_parent = title_el.find_parent('a') if title_el else None
                    if link_parent:
                        course_url = link_parent['href']

                item = {
                    "course_name": course_name,
                    "course_type": course_type,
                    "price_raw": price_offer,
                    "price_currency": "PEN" if "S/" in (price_offer + price_normal) else "USD",
                    "duration": duration,
                    "url": course_url,
                    # Extended fields for DMC as requested
                    "price_normal": price_normal,
                    "start_date": start_date
                }
                self.add_item(item)
            except Exception as e:
                print(f"Error parsing card: {e}")

        print(f"Successfully scraped {len(self.data)} courses.")

if __name__ == "__main__":
    scraper = DMCScraper()
    scraper.parse_catalog()
    scraper.save_data()
