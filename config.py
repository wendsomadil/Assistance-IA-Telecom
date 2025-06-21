# chatbot/config.py
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Répertoires d’entrée
PDF_DIRECTORY    = "C:/Users/HP/Citadel/id-fid-3/reglementation"
EXCEL_DIRECTORY  = "C:/Users/HP/Citadel/id-fid-3/output/excel"
WORD_DIRECTORY   = "C:/Users/HP/Citadel/id-fid-3/output/word"

# Chemin du fichier FAISS à la racine du projet
PROJECT_ROOT     = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
FAISS_INDEX_PATH = os.path.join(PROJECT_ROOT, "faiss_index.bin")

# Créer les dossiers de sortie si besoin
os.makedirs(EXCEL_DIRECTORY, exist_ok=True)
os.makedirs(WORD_DIRECTORY, exist_ok=True)

# Clé API pour Google Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("Erreur : la clé API n'a pas été chargée correctement.")
