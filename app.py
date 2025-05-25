# app.py
import streamlit as st
import os
import sys
import time
import base64
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from gtts import gTTS
import tempfile
import streamlit.components.v1 as components

# Modules internes
from chatbot.rag_pipeline import get_answer, search_faiss
from chatbot.utils import load_text_data
from chatbot.memory import ChatMemory
from chatbot.config import API_KEY, FAISS_INDEX_PATH

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'chatbot')))

# Configure la page
st.set_page_config(
    page_title="Assistance IA Télécom",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

texts = load_text_data()

# Encode image pour les logos
def encode_image_to_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return None

# Lecture vocale avec gTTS
def lire_texte_audio(text):
    tts = gTTS(text=text, lang='fr')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tts.save(tmp_file.name)
        st.audio(tmp_file.name, format='audio/mp3')

# Initialisation mémoire
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = ChatMemory()

# Charger CSS
def load_css(css_file):
    try:
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Fichier CSS introuvable.")

# Envoi de feedback par email
def envoyer_email(satisfaction, feedback):
    expediteur = "monappfeedback@gmail.com"
    mot_de_passe = "mill vwph cnue idej"
    destinataire = "wendsomadil@gmail.com"
    msg = MIMEText(f"Satisfaction : {satisfaction}/5\nCommentaire : {feedback}")
    msg["Subject"] = "Nouveau commentaire sur l'application"
    msg["From"] = expediteur
    msg["To"] = destinataire

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as serveur:
            serveur.starttls()
            serveur.login(expediteur, mot_de_passe)
            serveur.sendmail(expediteur, destinataire, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Erreur envoi email : {e}")
        return False

# Interface principale
def main():
    css_path = os.path.join(os.path.dirname(__file__), "css", "styles.css")
    load_css(css_path)

    st.markdown("<h1 class='main-title'>Assistance IA Télécom 📡</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Posez vos questions sur la réglementation des télécommunications au Burkina Faso</p>", unsafe_allow_html=True)

    # Logos
    ia_telecom_path = os.path.join("assets", "ia_telecom.png")
    citadel_path = os.path.join("assets", "citadel.png")
    col1, col2 = st.columns(2)
    with col1:
        encoded = encode_image_to_base64(ia_telecom_path)
        if encoded:
            st.markdown(f"<img src='data:image/png;base64,{encoded}' class='ia_telecom'>", unsafe_allow_html=True)
    with col2:
        encoded = encode_image_to_base64(citadel_path)
        if encoded:
            st.markdown(f"<img src='data:image/png;base64,{encoded}' class='citadel'>", unsafe_allow_html=True)

    # Thème
    theme = st.sidebar.radio("🎨 Thème", ["Clair", "Sombre"])
    st.markdown(f"<body data-theme='{ 'light' if theme == 'Clair' else 'dark' }'>", unsafe_allow_html=True)

    # Historique avec bouton vocal
    for idx, message in enumerate(st.session_state.chat_memory.history):
        user_html = f"""
            <div class='chat-container'>
                <div class='bubble user'>{message['user']}</div>
                <img class='avatar' src='https://i.imgur.com/IX8FzVb.png' />
            </div>
        """
        bot_html = f"""
            <div class='chat-container'>
                <img class='avatar' src='https://i.imgur.com/tfMZ5cD.png' />
                <div class='bubble bot'>{message['bot']}</div>
            </div>
        """
        st.markdown(user_html, unsafe_allow_html=True)
        st.markdown(bot_html, unsafe_allow_html=True)
        if st.button(f"🔊 Écouter la réponse {idx+1}", key=f"tts_{idx}"):
            lire_texte_audio(message["bot"])

    # Entrée utilisateur
    st.markdown("---")
    with st.form("chat_form", clear_on_submit=True):
        query = st.text_input("💬 Votre message :", placeholder="Tapez votre message ici...")
        submitted = st.form_submit_button("Envoyer")

    if submitted:
        if len(query.split()) >= 3:
            with st.spinner("💡 L'assistant réfléchit..."):
                search_results = search_faiss(query, top_n=5)
                faiss_context = "\n".join([doc for doc, _ in search_results])
                memory_context = "\n".join(st.session_state.chat_memory.get_context())
                full_context = f"{memory_context}\n\n{faiss_context}"
                response = get_answer(query, full_context)

                # Ajouter à l'historique
                st.session_state.chat_memory.add_to_memory(query, response)

                # Animation GPT tape
                placeholder = st.empty()
                display_text = ""
                for char in response:
                    display_text += char
                    placeholder.markdown(
                        f"""
                        <div class='chat-container'>
                            <img class='avatar' src='https://i.imgur.com/tfMZ5cD.png' />
                            <div class='bubble bot'>{display_text}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    time.sleep(0.01)

            st.rerun()
        else:
            st.warning("Veuillez entrer une question avec au moins trois mots.")

    # Effacer conversation
    st.markdown("---")
    if st.button("🧹 Effacer toute la conversation"):
        st.session_state.chat_memory.clear_memory()
        st.rerun()

    # Feedback
    st.markdown("---")
    st.header("📝 Donnez votre avis")
    satisfaction = st.slider("Satisfaction (1 = Pas du tout, 5 = Très satisfait)", 1, 5, 3)
    feedback = st.text_area("Commentaire libre")

    if st.button("📨 Envoyer le feedback"):
        df = pd.DataFrame({'satisfaction': [satisfaction], 'feedback': [feedback]})
        df.to_csv('feedback.csv', mode='a', header=False, index=False)
        if envoyer_email(satisfaction, feedback):
            st.success("Merci pour votre retour !")
        else:
            st.error("Échec lors de l'envoi de l'email.")

if __name__ == "__main__":
    main()

