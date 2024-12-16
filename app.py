# app.py
import streamlit as st
import os
from chatbot.rag_pipeline import get_answer, search_faiss
from chatbot.utils import load_text_data
from chatbot.memory import ChatMemory
import base64
import time

# Configurer le titre et les métadonnées de la page
st.set_page_config(
    page_title="Assistance IA Télécom",  # Titre de l'onglet du navigateur
    page_icon="📡",                     # Icône visible dans l'onglet
    layout="wide",                      # Largeur de la page (wide ou centered)
    initial_sidebar_state="expanded"    # État initial de la barre latérale
)

# Charger les textes extraits
texts = load_text_data()

# Fonction pour encoder une image en base64
def encode_image_to_base64(image_path):
    """Encode une image au format base64 pour l'injecter dans HTML"""
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
        except Exception as e:
            st.error(f"Erreur lors de l'encodage de l'image : {e}")
    return None

# Initialisation de la mémoire de conversation dans la session Streamlit
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = ChatMemory()

# Charger le CSS
def load_css(css_file):
    """Charge un fichier CSS externe"""
    try:
        with open(css_file, "r") as f:
            css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Fichier CSS introuvable. Assurez-vous qu'il est présent dans le répertoire approprié.")

# Interface principale
def main():
    # Charger le CSS
    css_path = os.path.join(os.path.dirname(__file__), "css", "styles.css")
    load_css(css_path)

    # Titre principal
    st.markdown("<h1 class='main-title'>Assistance IA Télécom 📡</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Posez vos questions sur la réglementation des télécommunications au Burkina Faso</p>", unsafe_allow_html=True)

    # Charger les images (ia_telecom + citadel)
    ia_telecom_path = os.path.join(os.path.dirname(__file__), "assets", "ia_telecom.png")
    citadel_path = os.path.join(os.path.dirname(__file__), "assets", "citadel.png")
    
    # Afficher les deux images côte à côte
    col1, col2 = st.columns(2)
    with col1:
        ia_telecom_encoded = encode_image_to_base64(ia_telecom_path)
        if ia_telecom_encoded:
            st.markdown(
                f"<img src='data:image/png;base64,{ia_telecom_encoded}' class='ia_telecom'>",
                unsafe_allow_html=True
            )
    with col2:
        citadel_encoded = encode_image_to_base64(citadel_path)
        if citadel_encoded:
            st.markdown(
                f"<img src='data:image/png;base64,{citadel_encoded}' class='citadel'>",
                unsafe_allow_html=True
            )

    # Boîte de question utilisateur    
    query = st.text_input(
        "Posez votre question :",
        help="Entrez une question d'au moins 3 mots pour obtenir une réponse."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Bouton pour envoyer la question
    if st.button("Envoyer la question", key="query_btn"):
        if len(query.split()) >= 3:
            with st.spinner("Recherche et génération de la réponse..."):
                # Ajout de barre de progression
                st.markdown("<div class='progress-bar'>", unsafe_allow_html=True)
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.02)
                    progress_bar.progress(i + 1)
                st.markdown("</div>", unsafe_allow_html=True)

                try:
                    # Recherche des résultats dans FAISS
                    search_results = search_faiss(query, top_n=5)
                    faiss_context = "\n".join([doc for doc, _ in search_results])

                    # Construire le contexte global (mémoire + FAISS)
                    memory_context = "\n".join(st.session_state.chat_memory.get_context())
                    full_context = f"{memory_context}\n\n{faiss_context}"

                    # Appeler `get_answer` avec la question et le contexte global
                    response = get_answer(query, full_context)

                    if response:                        
                        st.subheader("Réponse générée :")
                        st.markdown(f"<strong>{response}</strong>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                        # Enregistrer la conversation dans la mémoire
                        st.session_state.chat_memory.add_to_memory(query, response)
                    else:
                        st.error("Aucune réponse pertinente n'a été trouvée. Veuillez reformuler votre question.")
                except Exception as e:
                    st.error(f"Erreur lors du traitement de votre question : {e}")
        else:
            st.warning("Veuillez entrer une question contenant au moins trois mots.")

    # Afficher l'historique de la conversation
    with st.expander("Afficher l'historique de la conversation"):
        if st.session_state.chat_memory.history:
            for i, item in enumerate(st.session_state.chat_memory.history):
                st.markdown(f"**Question {i+1} :** {item['user']}")
                st.markdown(f"**Réponse {i+1} :** {item['bot']}")
        else:
            st.info("Aucun historique de conversation n'est disponible.")

    # Bouton pour effacer l'historique de la conversation
    if st.button("Effacer l'historique de la conversation"):
        st.session_state.chat_memory.clear_memory()
        st.success("Mémoire effacée.")

    # Section optionnelle pour afficher les textes sources
    with st.expander("Afficher les textes extraits (optionnel)"):
        if texts:
            for i, (file, content) in enumerate(texts.items()):
                st.markdown(f"### {file}")
                st.text_area(
                    "Contenu",
                    content[:1000],  # Limiter l'affichage à 1000 caractères
                    height=200,
                    key=f"text_area_{i}"  # Clé unique basé sur l'index
                )
        else:
            st.info("Aucun texte extrait n'est disponible. Assurez-vous que les fichiers Excel sont correctement chargés.")

# Point d'entrée principal
if __name__ == "__main__":
    main()
