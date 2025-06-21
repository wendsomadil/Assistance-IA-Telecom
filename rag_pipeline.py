# chatbot/rag_pipeline.py

import os
from functools import lru_cache

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# Modules internes
from chatbot.utils import load_text_data
from chatbot.config import API_KEY, FAISS_INDEX_PATH

# ——— Configuration Gemini ———
genai.configure(api_key=API_KEY)

# ——— Initialisation SentenceTransformer ———
encoder   = SentenceTransformer("all-MiniLM-L6-v2")
dimension = 384

# ——— Chargement ou création de l'index FAISS ———
if os.path.exists(FAISS_INDEX_PATH):
    index = faiss.read_index(FAISS_INDEX_PATH)
    print("Index FAISS chargé avec succès.")
else:
    index = faiss.IndexFlatL2(dimension)
    print("Nouvel index FAISS initialisé.")

# ——— Chargement des documents (Excel, Word, PDF) ———
texts     = load_text_data()          # {clé: texte brut}
documents = list(texts.values())      # liste de tous les textes
filenames = list(texts.keys())        # liste des clés (noms ou chemins)

# ——— Indexation si nécessaire ———
if index.ntotal == 0 and documents:
    embeddings = encoder.encode(documents, convert_to_numpy=True)
    index.add(embeddings)
    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"Index FAISS sauvegardé dans {FAISS_INDEX_PATH}.")

# === Étape 1 : Chunking sémantique ===
def semantic_chunking(text, max_tokens=300):
    chunks = []
    current, count = [], 0
    for sentence in text.split(". "):
        tokens = len(sentence.split())
        if count + tokens <= max_tokens:
            current.append(sentence)
            count += tokens
        else:
            chunks.append(" ".join(current))
            current, count = [sentence], tokens
    if current:
        chunks.append(" ".join(current))
    return chunks

# === Étape 2 : Recherche FAISS ===
def search_faiss(query, top_n=5):
    try:
        q_emb = encoder.encode([query], convert_to_numpy=True)
        distances, indices = index.search(q_emb, top_n)
        results = []
        for rank, idx in enumerate(indices[0]):
            if idx < len(documents):
                results.append((documents[idx], float(distances[0][rank])))
        return results
    except Exception as e:
        print(f"[search_faiss] Erreur : {e}")
        return []

# === Étape 3 : Décomposition de requête ===
def decompose_query(query):
    q = query.lower()
    if "compare" in q or "différences" in q:
        parts = query.split(" et ")
        return [f"Quels sont les détails concernant {p.strip()} ?" for p in parts]
    return [query]

# === Étape 4 : Fusion RRF ===
def reciprocal_rank_fusion(results_list, k=5):
    scores = {}
    for results in results_list:
        for rank, (chunk, _) in enumerate(results):
            scores[chunk] = scores.get(chunk, 0) + 1/(rank+1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]

# === Étape 5 : Formatage en tableau Markdown ===
def format_results_as_table(results):
    df = pd.DataFrame([
        {"Extrait": chunk[:100] + "...", "Score": round(score,4)}
        for chunk, score in results
    ])
    return df.to_markdown(index=False)

# === Étape 6 : Routage thématique ===
def route_query(query, subjects=None):
    if subjects is None:
        subjects = [
            "réglementation télécom", "licences", "concurrence",
            "droit des télécommunications", "neutralité du net",
            "fournisseurs d'accès internet", "fréquences radio",
            "protection des données personnelles", "autorités de régulation",
            "normes de qualité", "infractions réglementaires", "amendes",
            "accords internationaux", "aggréments", "équipements", "radioélectrique"
        ]
    lower = query.lower()
    for s in subjects:
        if s in lower:
            return s
    return "general"

# === Étape 7 : Génération avec Gemini ===
@lru_cache(maxsize=100)
def get_cached_answer(question, context=None):
    return generate_answer_with_gemini(question, context)

def generate_answer_with_gemini(question, context):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "Vous êtes un expert reconnu en réglementation télécom, droit des télécommunications, et politiques publiques "
            "au Burkina Faso. Vous êtes spécialisé dans les sujets couverts par l'ARCEP et votre rôle est d'informer "
            "avec des réponses :\n"
            "1. **Claires et structurées**, adaptées à une audience technique et légale.\n"
            "2. **Chiffrées**, avec des statistiques, données réelles et des comparaisons lorsque possible.\n"
            "3. **Documentées**, en citant des sources officielles telles que des décisions, arrêtés, lois ou directives "
            "pertinentes de l'ARCEP, incluant les références exactes.\n\n"
            "### Instructions spécifiques :\n"
            "Si le contexte est insuffisant, précisez quelles informations supplémentaires sont nécessaires pour fournir "
            "une réponse complète.\n\n"
            f"### Contexte disponible :\n{context}\n\n"
            f"### Question posée :\n{question}\n\n"
            "### Réponse complète de l'expert :\n"
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Erreur Gemini : {e}"

# === Étape Finale : Pipeline complet ===
def get_answer(question, context=None, metadata=None):
    # Sujet principal
    subject    = route_query(question)
    # Sous-requêtes
    subqs      = decompose_query(question)
    # Recherche et fusion
    results_ls = [search_faiss(sq, top_n=5) for sq in subqs]
    fused      = reciprocal_rank_fusion(results_ls)
    # Contexte combiné
    ctx_text   = "\n".join([chunk for chunk, _ in fused])
    if subject != "general":
        ctx_text = f"Contexte ({subject}) :\n{ctx_text}"
    # Retour tableau si demandé
    if any(w in question.lower() for w in ("comparer", "tableau")):
        return "Tableau :\n\n" + format_results_as_table(fused)
    # Générer
    return get_cached_answer(question, ctx_text)
