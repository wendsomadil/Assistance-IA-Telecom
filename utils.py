# chatbot/utils.py
import os
import pandas as pd
import fitz
import pdfplumber
from docx import Document
from chatbot.config import EXCEL_DIRECTORY, WORD_DIRECTORY, PDF_DIRECTORY

def load_text_data():
    """
    Parcourt les dossiers Excel, Word et PDF (récursivement) pour extraire
    tout le texte et le renvoyer sous forme de dict {clé: texte}.
    """
    texts = {}

    # 1. Excel (.xlsx)
    if os.path.isdir(EXCEL_DIRECTORY):
        for file in os.listdir(EXCEL_DIRECTORY):
            if file.lower().endswith(".xlsx"):
                path = os.path.join(EXCEL_DIRECTORY, file)
                try:
                    df = pd.read_excel(path, engine="openpyxl")
                    if "Content" in df.columns:
                        texts[file] = " ".join(df["Content"].dropna().astype(str))
                except Exception as e:
                    print(f"[Excel] Erreur sur {file} : {e}")

    # 2. Word (.docx)
    if os.path.isdir(WORD_DIRECTORY):
        for file in os.listdir(WORD_DIRECTORY):
            if file.lower().endswith(".docx"):
                path = os.path.join(WORD_DIRECTORY, file)
                try:
                    doc = Document(path)
                    full_text = [para.text for para in doc.paragraphs if para.text.strip()]
                    texts[file] = " ".join(full_text)
                except Exception as e:
                    print(f"[Word] Erreur sur {file} : {e}")

    # 3. PDF (récursif)
    if os.path.isdir(PDF_DIRECTORY):
        for root, dirs, files in os.walk(PDF_DIRECTORY):
            for file in files:
                if file.lower().endswith(".pdf"):
                    path = os.path.join(root, file)
                    key = os.path.relpath(path, PDF_DIRECTORY)
                    text = ""
                    try:
                        # 1) Lecture binaire et ouverture par flux
                        with open(path, "rb") as f:
                            pdf_bytes = f.read()
                        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                        pages = [page.get_text() for page in doc]
                        text = "\n".join(pages)
                    except Exception as e1:
                        print(f"[PDF][fitz] Erreur sur {key} : {e1}")
                        try:
                            # 2) Fallback avec pdfplumber
                            with pdfplumber.open(path) as pdf:
                                pages = [p.extract_text() or "" for p in pdf.pages]
                            text = "\n".join(pages)
                        except Exception as e2:
                            print(f"[PDF][pdfplumber] Échec sur {key} : {e2}")
                            continue  # on passe au fichier suivant
                    # Enfin on stocke le texte (même s'il est vide)
                    texts[key] = text

    return texts


def save_text_for_faiss(output_dir=None):
    """
    Sauvegarde chaque texte extrait en .txt dans le dossier `output_dir` (ou EXCEL_DIRECTORY par défaut).
    Utile pour inspection ou réindexation manuelle.
    """
    out_dir = output_dir or EXCEL_DIRECTORY
    os.makedirs(out_dir, exist_ok=True)

    for name, content in load_text_data().items():
        # Remplacer les barres par tirets pour un nom de fichier valide
        safe_name = name.replace(os.sep, "_")
        txt_path = os.path.join(out_dir, f"{safe_name}.txt")
        try:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"[Save] Impossible d'écrire {txt_path} : {e}")
