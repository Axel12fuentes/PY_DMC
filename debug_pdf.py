import pdfplumber

pdf_path = "scrapers/downloads/Explicit__Data_Analyst_IA.pdf"

try:
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            full_text += f"\n--- PAGE {i} ---\n{text}\n"
        
        print(full_text)
except Exception as e:
    print(f"Error: {e}")
