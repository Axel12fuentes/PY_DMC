import requests
from bs4 import BeautifulSoup
import re
from base_scraper import BaseScraper

class SmartDataScraper(BaseScraper):
    def __init__(self):
        super().__init__("SmartData")
        self.base_url = "https://smartdata.com.pe/cursos/"

    def get_urls(self):
        return [self.base_url]

    def parse_course(self, url):
        # Implementation for single course details if needed
        pass

    def parse_catalog(self):
        print(f"Fetching SmartData catalog from: {self.base_url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(self.base_url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching SmartData catalog: {e}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Based on analysis, courses are in .tutor-course elements
        course_cards = soup.select('.tutor-course')
        print(f"Found {len(course_cards)} SmartData course cards.")

        for card in course_cards:
            try:
                # Name
                title_el = card.select_one('.course-loop-title h2.title a, .tutor-course-title a')
                program_name = title_el.get_text(strip=True) if title_el else "N/A"
                if program_name == "N/A":
                    # Try finding any link with "curso" in href inside the card
                    any_link = card.select_one('a[href*="/curso/"]')
                    if any_link:
                        program_name = any_link.get_text(strip=True)
                
                if program_name == "N/A": continue

                # URL
                detail_url = title_el['href'] if title_el and title_el.has_attr('href') else "N/A"
                if detail_url == "N/A":
                    link_overlay = card.select_one('.link-overlay')
                    detail_url = link_overlay['href'] if link_overlay and link_overlay.has_attr('href') else "N/A"

                # Type
                # Yellow badge on image or within labels
                type_el = card.select_one('.tutor-course-loop-level, .badge-yellow, .tutor-course-label, .featured-label')
                # If not found, look for "ESPECIALIZACIÓN" text in badges
                badges = card.select('.tutor-meta-value, .featured-label')
                program_type = "Curso"
                for b in badges:
                    txt = b.get_text(strip=True).upper()
                    if "ESPECIALIZACIÓN" in txt or "DIPLOMA" in txt:
                        program_type = txt.capitalize()
                        break
                
                if program_type == "Curso" and "especializacion" in detail_url.lower():
                    program_type = "Especialización"
                
                # Check for explicit specialization label from analysis
                spec_label = card.select_one('.tutor-course-loop-level')
                if spec_label and "ESPECIALIZACIÓN" in spec_label.get_text(strip=True).upper():
                    program_type = "Especialización"

                # Modality
                # SmartData often indicates "En vivo" or "Online"
                modality = "Online" # Default
                content_text = card.get_text().lower()
                if "en vivo" in content_text:
                    modality = "En vivo"
                elif "grabado" in content_text:
                    modality = "Grabado"

                # Price
                price = "N/A"
                price_el = card.select_one('.price_desc, .tutor-price')
                if price_el:
                    price = price_el.get_text(strip=True)
                
                # Check for old price
                old_price_el = card.select_one('del')
                old_price = old_price_el.get_text(strip=True) if old_price_el else "N/A"

                # Duration
                duration = "N/A"
                duration_el = card.select_one('.tutor-course-loop-duration, .course-header-meta')
                if duration_el:
                    duration = duration_el.get_text(strip=True)

                # Level
                level = "N/A"
                level_el = card.select_one('.tutor-course-loop-level')
                if level_el:
                    level = level_el.get_text(strip=True)

                # Technologies
                # Usually logos on the image, might be harder to extract via BS4 text
                # We can check the description for mentions
                technologies = []
                tools = ["SQL", "Python", "Power BI", "Azure", "GCP", "AWS", "Fabric", "Pandas", "Spark"]
                for tool in tools:
                    if tool.lower() in content_text:
                        technologies.append(tool)
                
                tech_str = ", ".join(technologies) if technologies else "N/A"

                # Description
                description = "N/A"
                desc_el = card.select_one('.tutor-course-loop-excerpt, .tutor-course-content')
                if desc_el:
                    description = desc_el.get_text(strip=True)

                # Start Date
                start_date_el = card.select_one('.date-course')
                start_date = start_date_el.get_text(strip=True) if start_date_el else "N/A"

                item = {
                    "platform": "SmartData",
                    "course_type": program_type,
                    "course_name": program_name,
                    "modality": modality,
                    "price_raw": price,
                    "price_old": old_price,
                    "duration": duration,
                    "level": level,
                    "start_date": start_date,
                    "technologies": tech_str,
                    "url": detail_url,
                    "description": description
                }
                self.add_item(item)
            except Exception as e:
                print(f"Error parsing card: {e}")

        print(f"Successfully scraped {len(self.data)} SmartData courses.")

if __name__ == "__main__":
    scraper = SmartDataScraper()
    scraper.parse_catalog()
    scraper.save_data()
