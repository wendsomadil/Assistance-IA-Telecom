# chatbot/utils.py
import os
import pandas as pd
from docx import Document  # Importer python-docx pour traiter les fichiers .docx
from chatbot.config import EXCEL_DIRECTORY, WORD_DIRECTORY  # Assurez-vous d'ajouter WORD_DIRECTORY ici

def load_text_data():
    texts = {}

    # Charger les fichiers Excel
    for file in os.listdir(EXCEL_DIRECTORY):
        if file.endswith(".xlsx"):
            excel_path = os.path.join(EXCEL_DIRECTORY, file)
            try:
                df = pd.read_excel(excel_path, engine="openpyxl")
                if "Content" in df.columns:
                    texts[file] = " ".join(df["Content"].dropna())
            except Exception as e:
                print(f"Erreur lors du chargement de {file}: {e}")

    # Charger les fichiers Word
    for file in os.listdir(WORD_DIRECTORY):
        if file.endswith(".docx"):
            word_path = os.path.join(WORD_DIRECTORY, file)
            try:
                doc = Document(word_path)
                full_text = []
                for para in doc.paragraphs:
                    full_text.append(para.text)
                texts[file] = " ".join(full_text)  # Joindre le texte des paragraphes
            except Exception as e:
                print(f"Erreur lors du chargement de {file}: {e}")

    return texts

def save_text_for_faiss():
    """
    Sauvegarde le contenu textuel extrait dans des fichiers .txt pour FAISS.
    """
    for file, content in load_text_data().items():
        with open(os.path.join(EXCEL_DIRECTORY, f"{file}.txt"), "w", encoding="utf-8") as f:
            f.write(content)
