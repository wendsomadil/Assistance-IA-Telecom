# init_index.py
"""
Ce script initialise l'index FAISS en extrayant les données des fichiers sources 
(PDF/Excel) et en générant les embeddings nécessaires. 
Doit être exécuté avant d'utiliser l'application principale.
"""

import os
import faiss
from sentence_transformers import SentenceTransformer
from chatbot.extraction import process_pdfs_in_directory
from chatbot.utils import load_text_data
from chatbot.config import FAISS_INDEX_PATH
from chatbot.config import PDF_DIRECTORY, EXCEL_DIRECTORY

def create_faiss_index(embedding_dim=384):
    """Initialise un index FAISS avec une dimension spécifique."""
    return faiss.IndexFlatL2(embedding_dim)

def index_documents_with_faiss(texts, encoder, index):
    """Génère des embeddings pour les textes et les indexe dans FAISS."""
    documents = list(texts.values())
    embeddings = encoder.encode(documents, convert_to_numpy=True)
    index.add(embeddings)
    return index

if __name__ == "__main__":
    # Extraction des données des PDFs
    process_pdfs_in_directory()

    # Chargement des textes extraits
    texts = load_text_data()

    if not texts:
        print("Aucun texte trouvé à indexer. Vérifiez vos fichiers source.")
        exit(1)

    # Initialisation de l'index FAISS
    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    embedding_dim = 384
    faiss_index = create_faiss_index(embedding_dim)

    # Indexation des documents
    faiss_index = index_documents_with_faiss(texts, encoder, faiss_index)

    # Sauvegarde de l'index FAISS
    faiss.write_index(faiss_index, FAISS_INDEX_PATH)
    print(f"Index FAISS sauvegardé dans : {FAISS_INDEX_PATH}")
