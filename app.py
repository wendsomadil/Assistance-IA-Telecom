# app.py
import streamlit as st
import os
import sys
import time
import base64
import pandas as pd
import smtplib
from email.mime.text import MIMEText

# Importer les modules de votre application
from chatbot.rag_pipeline import get_answer, search_faiss
from chatbot.utils import load_text_data
from chatbot.memory import ChatMemory
from chatbot.config import API_KEY, FAISS_INDEX_PATH

# Ajouter le répertoire 'chatbot' au sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'chatbot')))

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
    """Encode une image au format base64 pour l'injecter dans le HTML."""
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
    """Charge un fichier CSS externe."""
    try:
        with open(css_file, "r") as f:
            css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Fichier CSS introuvable. Assurez-vous qu'il est présent dans le répertoire approprié.")

# Fonction pour envoyer un email avec le feedback de l'utilisateur
def envoyer_email(satisfaction, feedback):
    """
    Envoie un email contenant la note et le commentaire de l'utilisateur.
    
    ⚠️ Remplacez les valeurs ci-dessous par celles de votre compte dédié.
    """
    # Informations du compte dédié (compte Gmail dédié par exemple)
    expediteur = "monappfeedback@gmail.com"       # Remplacez par l'adresse email de votre compte dédié
    mot_de_passe = "mill vwph cnue idej"    # Remplacez par votre mot de passe d'application
    destinataire = "wendsomadil@gmail.com"               # Votre adresse email de réception
    sujet = "Nouveau commentaire sur l'application"
    
    contenu = f"""
    Nouvelle évaluation reçue :
    ⭐ Satisfaction : {satisfaction}/5
    💬 Commentaire : {feedback}
    """
    
    msg = MIMEText(contenu)
    msg["Subject"] = sujet
    msg["From"] = expediteur
    msg["To"] = destinataire

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as serveur:
            serveur.starttls()
            serveur.login(expediteur, mot_de_passe)
            serveur.sendmail(expediteur, destinataire, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'envoi de l'email : {e}")
        return False

# Interface principale de l'application
def main():
    # Charger le CSS personnalisé
    css_path = os.path.join(os.path.dirname(__file__), "css", "styles.css")
    load_css(css_path)

    # Titre et sous-titre de l'application
    st.markdown("<h1 class='main-title'>Assistance IA Télécom 📡</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Posez vos questions sur la réglementation des télécommunications au Burkina Faso</p>", unsafe_allow_html=True)

    # Chargement et affichage des images (ia_telecom et citadel)
    ia_telecom_path = os.path.join(os.path.dirname(__file__), "assets", "ia_telecom.png")
    citadel_path = os.path.join(os.path.dirname(__file__), "assets", "citadel.png")
    
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

    # Zone de saisie pour la question de l'utilisateur
    query = st.text_input(
        "Posez votre question :",
        help="Entrez une question d'au moins 3 mots pour obtenir une réponse."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Bouton pour envoyer la question
    if st.button("Envoyer la question", key="query_btn"):
        if len(query.split()) >= 3:
            with st.spinner("Recherche et génération de la réponse..."):
                # Affichage d'une barre de progression
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

                    # Création du contexte global (historique + résultats FAISS)
                    memory_context = "\n".join(st.session_state.chat_memory.get_context())
                    full_context = f"{memory_context}\n\n{faiss_context}"

                    # Récupération de la réponse générée
                    response = get_answer(query, full_context)

                    if response:
                        st.subheader("Réponse générée :")
                        st.markdown(f"<strong>{response}</strong>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                        # Sauvegarde de la conversation en mémoire
                        st.session_state.chat_memory.add_to_memory(query, response)
                    else:
                        st.error("Aucune réponse pertinente n'a été trouvée. Veuillez reformuler votre question.")
                except Exception as e:
                    st.error(f"Erreur lors du traitement de votre question : {e}")
        else:
            st.warning("Veuillez entrer une question contenant au moins trois mots.")

    # Affichage de l'historique de la conversation
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

    # Formulaire d'évaluation et de commentaires
    st.markdown("---")  # Séparateur visuel
    st.header("Votre avis nous intéresse !")
    satisfaction = st.slider("À quel point êtes-vous satisfait de l'expérience ?", min_value=1, max_value=5)
    feedback = st.text_area("Vos commentaires:")

    if st.button("Envoyer"):
        # Enregistrement optionnel dans un fichier CSV
        data = {'satisfaction': satisfaction, 'feedback': feedback}
        df = pd.DataFrame(data, index=[0])
        df.to_csv('feedback.csv', mode='a', header=False, index=False)
        
        # Envoi de l'email contenant le feedback
        if envoyer_email(satisfaction, feedback):
            st.success("Vos commentaires ont bien été envoyés par email !")
        else:
            st.error("Une erreur est survenue lors de l'envoi de l'email.")

# Point d'entrée principal
if __name__ == "__main__":
    main()
