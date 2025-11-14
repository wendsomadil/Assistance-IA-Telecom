# chatbot/rag_pipeline.py
import os
import faiss
import numpy as np
import pandas as pd  # Pour formater les tableaux
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from chatbot.utils import load_text_data
from chatbot.config import API_KEY, FAISS_INDEX_PATH
from functools import lru_cache

# Configuration globale
genai.configure(api_key=API_KEY)

# Initialisation du modèle SentenceTransformer
encoder = SentenceTransformer("all-MiniLM-L6-v2")
dimension = 384

# Chargement ou création de l'index FAISS
if os.path.exists(FAISS_INDEX_PATH):
    index = faiss.read_index(FAISS_INDEX_PATH)
    print("Index FAISS chargé avec succès.")
else:
    index = faiss.IndexFlatL2(dimension)
    print("Nouvel index FAISS initialisé.")

# Chargement des documents et des embeddings dans FAISS
texts = load_text_data()
documents = list(texts.values())
filenames = list(texts.keys())

if index.ntotal == 0 and documents:
    embeddings = encoder.encode(documents, convert_to_numpy=True)
    index.add(embeddings)
    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"Index FAISS sauvegardé dans {FAISS_INDEX_PATH}.")


### --- Étape 1 : Chunking Sémantique --- ###
def semantic_chunking(text, max_tokens=300):
    """
    Découpe un document en chunks optimisés pour le traitement.
    """
    chunks = []
    current_chunk = []
    token_count = 0

    for sentence in text.split(". "):  # Utilisation basique
        tokens = len(sentence.split())
        if token_count + tokens <= max_tokens:
            current_chunk.append(sentence)
            token_count += tokens
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            token_count = tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


### --- Étape 2 : Recherche avec FAISS --- ###
def search_faiss(query, top_n=5):
    """
    Recherche les documents les plus similaires pour une requête.
    """
    try:
        query_embedding = encoder.encode([query], convert_to_numpy=True)
        distances, indices = index.search(query_embedding, top_n)
        return [(documents[i], distances[0][j]) for j, i in enumerate(indices[0]) if i < len(documents)]
    except Exception as e:
        print(f"Erreur lors de la recherche FAISS : {str(e)}")
        return []


### --- Étape 3 : Décomposition des Requêtes --- ###
def decompose_query(query):
    """
    Divise une requête complexe en sous-questions.
    """
    if "compare" in query.lower() or "différences" in query.lower():
        items = query.split(" et ")
        return [f"Quels sont les détails concernant {item.strip()} ?" for item in items]
    return [query]


def reciprocal_rank_fusion(results_list, k=5):
    """
    Fusion des résultats avec la méthode RRF.
    """
    scores = {}
    for results in results_list:
        for rank, (chunk, score) in enumerate(results):
            rank_score = 1 / (rank + 1)  # Scoring RRF
            scores[chunk] = scores.get(chunk, 0) + rank_score

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]


### --- Étape 4 : Formatage des Résultats --- ###
def format_results_as_table(results):
    """
    Retourne un tableau Markdown formaté des résultats.
    """
    data = [{"Extrait": chunk[:100] + "...", "Score": round(score, 4)} for chunk, score in results]
    df = pd.DataFrame(data)
    return df.to_markdown(index=False)


### --- Étape 5 : Routage des Questions --- ###
def route_query(query, subjects=None):
    """
    Identifie le sujet principal d'une requête pour le routage.
    """
    if not subjects:
        subjects = [
            "réglementation télécom", "licences", "concurrence", "droit des télécommunications",
            "neutralité du net", "fournisseurs d'accès internet", "fréquences radio",
            "protection des données personnelles", "autorités de régulation",
            "normes de qualité", "infractions réglementaires", "amendes",
            "accords internationaux", "aggréments", "équipements", "radioélectrique"
        ]
    for subject in subjects:
        if subject in query.lower():
            return subject
    return "general"


### --- Étape 6 : Génération avec Gemini --- ###
@lru_cache(maxsize=100)
def get_cached_answer(question, context=None):
    """
    Génère et met en cache une réponse à l'aide de Gemini.
    """
    return generate_answer_with_gemini(question, context)


def generate_answer_with_gemini(question, context):
    """
    Génère une réponse détaillée et chiffrée en utilisant l'API Gemini avec un contexte donné.
    L'expert fournit des informations chiffrées et cite des décisions, lois, réglementations ou arrêtés pertinents de l'ARCEP.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        # Prompt amélioré pour guider Gemini
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
        return f"Erreur avec Gemini : {str(e)}"
        

### --- Étape Finale : Pipeline Complet --- ###
def get_answer(question, context=None, metadata=None):
    """
    Exécute l'ensemble du pipeline pour générer une réponse.
    """
    # Identifier le sujet principal
    subject = route_query(question)

    # Décomposer la question en sous-questions et récupérer les résultats
    subqueries = decompose_query(question)
    results_list = [search_faiss(subquery, top_n=5) for subquery in subqueries]

    # Fusionner les résultats
    fused_results = reciprocal_rank_fusion(results_list)
    context = "\n".join([doc for doc, _ in fused_results])

    # Ajouter un contexte spécifique si le sujet est identifié
    if subject != "general":
        context = f"Contexte spécifique à {subject} :\n{context}"

    # Vérifier si un tableau est requis
    if "comparer" in question.lower() or "tableau" in question.lower():
        table = format_results_as_table(fused_results)
        return f"Voici un tableau récapitulatif des résultats :\n\n{table}"

    # Générer la réponse avec Gemini
    return get_cached_answer(question, context)
