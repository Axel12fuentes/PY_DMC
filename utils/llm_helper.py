import os
import pdfplumber
import json
from openai import OpenAI
from dotenv import load_dotenv

class LLMHelper:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            print("Warning: OPENAI_API_KEY not found in environment.")

    def extract_from_pdf(self, pdf_path):
        """
        Extracts structured course info from a PDF brochure using GPT-4o-mini.
        Returns a dict with duration, start_date, certification, methodology, instructor, content.
        """
        if not self.client:
            return {}

        try:
            full_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                # Extract first 5 and last 3 pages
                pages_to_extract = pdf.pages[:5]
                if len(pdf.pages) > 5:
                    pages_to_extract += pdf.pages[-3:]
                
                seen_pages = set()
                for page in pages_to_extract:
                    if page.page_number in seen_pages: continue
                    seen_pages.add(page.page_number)
                    
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
            
            if not full_text.strip():
                return {}

            prompt = f"""
            You are a data extraction assistant. Extract the following information from the provided course brochure text:
            1. Duration (in Academic Hours or similar)
            2. Start Date (Look for "Inicio", "Start", specific dates like "21 Enero")
            3. Certification (How many and what certificates?)
            4. Methodology (Brief summary)
            5. Instructor Experience (Brief summary)
            6. Content Summary (Brief summary of modules/topics)

            Return ONLY raw JSON with keys: duration, start_date, certification, methodology, instructor, content.
            If a field is not found, use "N/A".
            
            Brochure Text:
            {full_text[:10000]} 
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data from text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )

            content = response.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            
            try:
                data = json.loads(content)
            except:
                data = {}
            
            return {
                "duration": data.get("duration", "N/A"),
                "start_date": data.get("start_date", "N/A"),
                "certification": data.get("certification", "N/A"),
                "methodology": data.get("methodology", "N/A"),
                "instructor": data.get("instructor", "N/A"),
                "content": data.get("content", "N/A")
            }

        except Exception as e:
            print(f"LLM Helper Error: {e}")
            return {}

    def extract_from_html(self, html_content, url=""):
        """
        Extracts structured course info from HTML using GPT-4o-mini.
        This is more robust than selector-based scraping.
        Returns a dict with course_name, price_raw, price_original, duration, etc.
        """
        if not self.client:
            return {}

        try:
            # Limit HTML size to avoid token overflow
            # Remove script/style tags content first
            import re
            clean_html = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
            clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL)
            
            # Take first 15000 chars (reasonable for most course pages)
            clean_html = clean_html[:15000]

            prompt = f"""
            You are a web scraping assistant. Extract course information from the provided HTML.
            
            Extract the following fields:
            1. course_name: The main course/program title
            2. price_raw: Current price (with currency symbol, e.g., "S/480" or "$200")
            3. price_original: Original/regular price if shown (often crossed out or labeled "Antes")
            4. duration: Course duration (e.g., "120 horas", "8 semanas")
            5. start_date: When the course starts
            6. course_type: Type of program (Bootcamp, Especialización, Curso, Diplomado, etc.)
            7. instructor: Instructor name if visible
            8. modality: Online, Presencial, Híbrido, En vivo, etc.
            
            Return ONLY raw JSON with these keys. Use "N/A" if a field is not found.
            
            URL: {url}
            
            HTML (truncated):
            {clean_html}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data from HTML."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )

            content = response.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            
            try:
                data = json.loads(content)
            except:
                data = {}
            
            return {
                "course_name": data.get("course_name", "N/A"),
                "price_raw": data.get("price_raw", "N/A"),
                "price_original": data.get("price_original", "N/A"),
                "duration": data.get("duration", "N/A"),
                "start_date": data.get("start_date", "N/A"),
                "course_type": data.get("course_type", "Curso"),
                "instructor": data.get("instructor", "N/A"),
                "modality": data.get("modality", "N/A")
            }

        except Exception as e:
            print(f"HTML Extraction Error: {e}")
            return {}
