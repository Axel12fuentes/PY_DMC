import pandas as pd
from abc import ABC, abstractmethod
import os

class BaseScraper(ABC):
    def __init__(self, source_name):
        self.source_name = source_name
        self.data = []

    @abstractmethod
    def get_urls(self):
        """Recover all course URLs from the main catalog."""
        pass

    @abstractmethod
    def parse_course(self, url):
        """Extract details from a specific course URL."""
        pass

    def add_item(self, item):
        """Normalize and add an item to the data list."""
        defaults = {
            "source_site": self.source_name,
            "course_name": "N/A",
            "course_type": "N/A",
            "price_raw": "N/A",
            "price_currency": "N/A",
            "instructor": "N/A",
            "duration": "N/A",
            "syllabus_content": "N/A",
            "certification_type": "N/A",
            "brochure_url": "N/A",
            "url": "N/A"
        }
        # Update defaults with actual item data
        normalized_item = {**defaults, **item}
        self.data.append(normalized_item)

    def save_data(self, output_dir="output"):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filename = os.path.join(output_dir, f"{self.source_name.lower().replace(' ', '_')}_database.csv")
        df = pd.DataFrame(self.data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"Data saved to {filename}")
        return filename
