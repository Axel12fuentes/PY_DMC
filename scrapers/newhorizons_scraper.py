"""
New Horizons Scraper usando la estrategia LLM-HTML
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.universal_scraper import UniversalScraper

if __name__ == "__main__":
    scraper = UniversalScraper(
        site_name="NewHorizons",
        catalog_url="https://www.newhorizons.edu.pe/",
        download_dir_name="newhorizons"
    )
    scraper.parse_catalog()
    scraper.save_data()
