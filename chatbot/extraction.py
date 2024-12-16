# chatbot/extraction.py
import os
import pandas as pd
import re
from pdf2image import convert_from_path
import pytesseract
import fitz  # PyMuPDF
import pdfplumber
from config import PDF_DIRECTORY, EXCEL_DIRECTORY
import sys

# Ajouter le répertoire racine de votre projet au PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Définir le chemin vers Poppler
POPPLER_PATH = r"C:\Program Files\Poppler\poppler-24.08.0\Library\bin"

# Paramètres supplémentaires
DEFAULT_LANGUAGE = "eng+fra"
IMAGE_RESOLUTION = 300
IGNORE_EMPTY_FILES = True
SAVE_RAW_TEXT = True


def extract_text_from_pdf_pymupdf(pdf_path):
    """Extraire du texte avec PyMuPDF"""
    text_by_page = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            text_by_page.append(text.strip())
            print(f"Page {page_num + 1} extraite (PyMuPDF) :\n{text[:500]}...")
    except Exception as e:
        print(f"Erreur lors de l'extraction avec PyMuPDF pour {pdf_path}: {e}")
    return text_by_page


def extract_text_from_pdf_pdfplumber(pdf_path):
    """Extraire du texte avec pdfplumber (utile pour les tables et mises en page complexes)"""
    text_by_page = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in range(len(pdf.pages)):
                page = pdf.pages[page_num]
                text = page.extract_text()
                if text:
                    text_by_page.append(text.strip())
                print(f"Page {page_num + 1} extraite (pdfplumber) :\n{text[:500]}...")
    except Exception as e:
        print(f"Erreur lors de l'extraction avec pdfplumber pour {pdf_path}: {e}")
    return text_by_page


def extract_text_from_scanned_pdf(pdf_path, language=DEFAULT_LANGUAGE, resolution=IMAGE_RESOLUTION):
    """Extraire du texte à partir de PDF scannés via OCR"""
    text_by_page = []
    try:
        pages = convert_from_path(pdf_path, resolution, poppler_path=POPPLER_PATH)
        for i, page in enumerate(pages):
            text = pytesseract.image_to_string(page, lang=language)
            text_by_page.append(text.strip())
            print(f"Page {i + 1} extraite via OCR :\n{text[:500]}...")
    except Exception as e:
        print(f"Erreur lors de l'OCR pour {pdf_path}: {e}")
    return text_by_page


def clean_text(text):
    """Nettoie le texte extrait en supprimant les espaces multiples et autres artefacts"""
    text = re.sub(r'\s+', ' ', text)  # Remplacer les espaces multiples par un seul espace
    text = text.strip()
    return text


def extract_articles_and_content(text):
    """Extrait les articles et leur contenu à partir du texte"""
    articles = []
    pattern = re.compile(r"(Article \d+)(.*?)(?=Article \d+|$)", re.DOTALL)
    matches = pattern.findall(text)
    for match in matches:
        article = match[0].strip()
        content = match[1].strip()
        articles.append((article, content))
    return articles


def extract_sections_and_titles(text):
    """Extrait les chapitres, sections, titres à partir du texte"""
    data = []
    chapter_pattern = re.compile(r"(Chapitre \d+)(.*?)(?=Chapitre \d+|$)", re.DOTALL)
    section_pattern = re.compile(r"(Section \d+)(.*?)(?=Section \d+|$)", re.DOTALL)
    title_pattern = re.compile(r"(Titre [\dIVXLCD]+)(.*?)(?=Titre [\dIVXLCD]+|$)", re.DOTALL)

    for chapter in chapter_pattern.findall(text):
        data.append(("Chapitre", chapter[0].strip(), chapter[1].strip()))
    for section in section_pattern.findall(text):
        data.append(("Section", section[0].strip(), section[1].strip()))
    for title in title_pattern.findall(text):
        data.append(("Titre", title[0].strip(), title[1].strip()))
    return data


def extract_parts_and_paragraphs(text):
    """Extrait les parties numérotées et les paragraphes du texte"""
    parts = []
    paragraphs = []

    # Détection des parties numérotées
    part_pattern = re.compile(r"(Partie \d+|Part \d+|Section \d+|[\d]+[.)]\s+.*?)", re.DOTALL)
    matches = part_pattern.split(text)

    for i in range(1, len(matches), 2):
        part_title = matches[i].strip()
        part_content = matches[i + 1].strip() if i + 1 < len(matches) else ""
        parts.append((part_title, part_content))

    # Extraction des paragraphes
    paragraph_pattern = re.compile(r"(\n\s*\n|(\.\s))")
    raw_paragraphs = paragraph_pattern.split(text)
    paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]
    return parts, paragraphs

def extract_tables_from_pdf(pdf_path):
    """Extraire les tableaux à partir du PDF avec pdfplumber"""
    tables_by_page = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in range(len(pdf.pages)):
                page = pdf.pages[page_num]
                tables = page.extract_tables()
                tables_by_page.append(tables)
                print(f"Page {page_num + 1} : {len(tables)} tableau(x) extrait(s) (pdfplumber).")
    except Exception as e:
        print(f"Erreur lors de l'extraction des tableaux avec pdfplumber pour {pdf_path}: {e}")
    return tables_by_page

def extract_image_tables_with_ocr(pdf_path, resolution=300, language=DEFAULT_LANGUAGE):
    """Extraire les tableaux sous forme d'images et appliquer l'OCR"""
    tables_by_page = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extraire les images de la page
                images = page.images
                if not images:
                    continue
                
                ocr_tables = []
                for image_index, image in enumerate(images):
                    # Extraire la zone de l'image
                    bbox = (image['x0'], image['top'], image['x1'], image['bottom'])
                    cropped_image = page.to_image(resolution=resolution).crop(bbox)
                    
                    # Appliquer OCR à l'image
                    ocr_text = pytesseract.image_to_string(cropped_image.original, lang=language)
                    
                    # Convertir l'OCR en structure tabulaire
                    table = parse_ocr_text_to_table(ocr_text)
                    if table:
                        ocr_tables.append(table)
                
                tables_by_page.append(ocr_tables)
                print(f"Page {page_num + 1} : {len(ocr_tables)} tableau(x) OCRisé(s) extrait(s).")
    except Exception as e:
        print(f"Erreur lors de l'extraction OCR des tableaux d'images pour {pdf_path}: {e}")
    return tables_by_page


def parse_ocr_text_to_table(ocr_text):
    """Convertir le texte OCRisé en une structure tabulaire"""
    # Diviser le texte OCRisé en lignes
    lines = ocr_text.split("\n")
    table = []
    
    for line in lines:
        # Déterminer les colonnes en utilisant des séparateurs
        columns = re.split(r'\t+|\s{2,}|,', line)
        if any(columns):  # Filtrer les lignes vides
            table.append([col.strip() for col in columns if col.strip()])
    
    # Retourner la structure tabulaire si elle semble valide
    if len(table) > 1 and any(len(row) > 1 for row in table):
        return table
    return None

def extract_custom_parts(text, custom_patterns):
    """Extrait des parties personnalisées définies par des patterns"""
    custom_data = []
    for label, pattern in custom_patterns.items():
        compiled_pattern = re.compile(pattern, re.DOTALL)
        matches = compiled_pattern.findall(text)
        for match in matches:
            title = match[0].strip()
            content = match[1].strip() if len(match) > 1 else ""
            custom_data.append((label, title, content))
    return custom_data


# Modifiez les regex ici pour personnaliser l'extraction
custom_patterns = {
    "Partie": r"(Partie \d+|Part \d+)(.*?)(?=Partie \d+|Part \d+|$)",
    "Sous-Partie": r"(Sous-partie \d+|Sous-section \d+)(.*?)(?=Sous-partie \d+|Sous-section \d+|$)",
    "Article étendu": r"(Article \d+-\d+)(.*?)(?=Article \d+-\d+|$)",
}


def process_pdfs_in_directory():
    """Parcourt les PDF dans un répertoire et extrait les informations vers des fichiers Excel"""
    os.makedirs(EXCEL_DIRECTORY, exist_ok=True)
    print("🚀 Début de l'extraction des fichiers PDF.")
    
    for pdf_file in os.listdir(PDF_DIRECTORY):
        pdf_path = os.path.join(PDF_DIRECTORY, pdf_file)
        
        if os.path.isfile(pdf_path) and pdf_file.endswith(".pdf"):
            print(f"📄 Traitement du fichier : {pdf_path}")
            text_by_page = []

            for method in [extract_text_from_pdf_pymupdf, extract_text_from_pdf_pdfplumber, extract_text_from_scanned_pdf]:
                try:
                    text_by_page = method(pdf_path)
                    if any(text_by_page):
                        break
                except Exception as e:
                    print(f"Erreur avec {method.__name__}: {e}")

            if not text_by_page:
                print(f"❌ Aucun texte extrait pour {pdf_file}.")
                continue

            # Nettoyage et extraction
            cleaned_pages = [clean_text(page) for page in text_by_page]
            all_text = " ".join(cleaned_pages)
            
            # Extraction des données structurées
            articles = extract_articles_and_content(all_text)
            sections_and_titles = extract_sections_and_titles(all_text)
            parts, paragraphs = extract_parts_and_paragraphs(all_text)
            custom_data = extract_custom_parts(all_text, custom_patterns)
            
            # Extraction des tableaux texte
            tables_by_page = extract_tables_from_pdf(pdf_path)
            
            # Extraction des tableaux images via OCR
            image_tables_by_page = extract_image_tables_with_ocr(pdf_path)

            # Sauvegarde
            excel_file = os.path.join(EXCEL_DIRECTORY, f"{pdf_file}.xlsx")
            with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
                if articles:
                    pd.DataFrame(articles, columns=["Article", "Content"]).to_excel(writer, sheet_name="Articles", index=False)
                if sections_and_titles:
                    pd.DataFrame(sections_and_titles, columns=["Type", "Label", "Content"]).to_excel(writer, sheet_name="Sections et Titres", index=False)
                if parts:
                    pd.DataFrame(parts, columns=["Partie", "Contenu"]).to_excel(writer, sheet_name="Parties", index=False)
                if paragraphs:
                    pd.DataFrame(paragraphs, columns=["Paragraphe"]).to_excel(writer, sheet_name="Paragraphes", index=False)
                if custom_data:
                    pd.DataFrame(custom_data, columns=["Type", "Titre", "Contenu"]).to_excel(writer, sheet_name="Données personnalisées", index=False)
                
                # Sauvegarder les tableaux texte
                for page_num, tables in enumerate(tables_by_page):
                    for table_index, table in enumerate(tables):
                        df = pd.DataFrame(table[1:], columns=table[0])  # La première ligne comme en-tête
                        sheet_name = f"Tableau {page_num + 1}_{table_index + 1}"
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Sauvegarder les tableaux images OCRisés
                for page_num, image_tables in enumerate(image_tables_by_page):
                    for table_index, table in enumerate(image_tables):
                        df = pd.DataFrame(table)
                        sheet_name = f"Table OCR {page_num + 1}_{table_index + 1}"
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"✅ Fichier Excel créé : {excel_file}")


if __name__ == "__main__":
    process_pdfs_in_directory()
