# chatbot/config.py
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Définir les répertoires pour les fichiers PDF et Excel
PDF_DIRECTORY = "C:/Users/HP/Citadel/id-fid-3/pdf_files" 
EXCEL_DIRECTORY = "C:/Users/HP/Citadel/id-fid-3/output/excel"
FAISS_INDEX_PATH = os.path.join(EXCEL_DIRECTORY, "faiss_index.bin")

# Créer le répertoire Excel si nécessaire
if not os.path.exists(EXCEL_DIRECTORY):
    os.makedirs(EXCEL_DIRECTORY)

# Clé API pour Google Gemini (si utilisée)
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("Erreur : la clé API n'a pas été chargée correctement.")
else:
    print(f"Clé API : {API_KEY}")
