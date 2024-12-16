# chatbot/embedding_model.py
from sentence_transformers import SentenceTransformer

def get_encoder(model_name="all-MiniLM-L6-v2"):
    """
    Initialise et retourne le modèle d'encodage.
    """
    return SentenceTransformer(model_name)
