# acceuil.py (page principale)
import streamlit as st
import os, sys, time, base64, tempfile
from gtts import gTTS
from chatbot.rag_pipeline import get_answer, search_faiss
from chatbot.utils import load_text_data
from chatbot.memory import ChatMemory
from streamlit_option_menu import option_menu

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'chatbot')))

# Config de la page
st.set_page_config(page_title="Assistance IA Télécom", page_icon="📡", layout="wide")

# Charger les données et initialiser la mémoire
texts = load_text_data()
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = ChatMemory()
if "theme" not in st.session_state:
    st.session_state.theme = "light"  # Thème par défaut
if "lang" not in st.session_state:
    st.session_state.lang = "fr"      # Langue par défaut

# Fonction utilitaire pour encoder une image en base64 (pour les logos)
def encode_image_to_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return None

# Fonction text-to-speech avec gTTS
def lire_texte_audio(text):
    tts = gTTS(text=text, lang= 'fr' if st.session_state.lang == "fr" else 'en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tts.save(tmp_file.name)
        st.audio(tmp_file.name, format='audio/mpeg')  # Diffusion audio du fichier MP3:contentReference[oaicite:2]{index=2}

# Chargement de la feuille de style (styles.css)
def load_css(css_file):
    if os.path.exists(css_file):
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
css_path = os.path.join(os.path.dirname(__file__), "css", "styles.css")
load_css(css_path)

# Affichage de l’en-tête (logos + titre + sous-titre)
ia_encoded = encode_image_to_base64(os.path.join("assets", "ia_telecom.png"))
citadel_encoded = encode_image_to_base64(os.path.join("assets", "citadel.png"))
# Texte dynamique selon la langue
if st.session_state.lang == "fr":
    title = "Assistance IA Télécom 📡"
    subtitle = "Posez vos questions sur la réglementation des télécommunications au Burkina Faso"
else:
    title = "Telecom AI Assistance 📡"
    subtitle = "Ask your questions about telecommunications regulation in Burkina Faso"
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <img src="data:image/png;base64,{ia_encoded}" style="height: 40px;" />
        <div style="text-align: center; flex-grow: 1;">
            <h1 style="margin-bottom: 0;">{title}</h1>
            <p style="margin-top: 4px;">{subtitle}</p>
        </div>
        <img src="data:image/png;base64,{citadel_encoded}" style="height: 40px;" />
    </div>
""", unsafe_allow_html=True)

# Appliquer le thème enregistré
theme = st.session_state.get("theme", "light")
st.markdown(f"<body data-theme='{theme}'>", unsafe_allow_html=True)

# Affichage de chaque message de l’historique (bulles CSS)
for idx, message in enumerate(st.session_state.chat_memory.history):
    # Bulle utilisateur
    st.markdown(f"""
        <div class='chat-container'>
            <div class='bubble user'>{message['user']}</div>
            <img class='avatar' src='https://i.imgur.com/IX8FzVb.png' />
        </div>
    """, unsafe_allow_html=True)
    # Bulle bot
    st.markdown(f"""
        <div class='chat-container'>
            <img class='avatar' src='https://i.imgur.com/tfMZ5cD.png' />
            <div class='bubble bot'>{message['bot']}</div>
        </div>
    """, unsafe_allow_html=True)
    # Bouton pour écouter la réponse (TTS)
    listen_text = "🔊 Listen to answer" if st.session_state.lang == "en" else "🔊 Écouter la réponse"
    if st.button(f"{listen_text} {idx+1}", key=f"tts_{idx}"):
        lire_texte_audio(message["bot"])

st.markdown("---")

# Formulaire de saisie de l’utilisateur
with st.form("chat_form", clear_on_submit=True):
    if st.session_state.lang == "fr":
        query = st.text_input("💬 Votre message :", placeholder="Tapez votre message ici...")
        submit_text = "Envoyer"
    else:
        query = st.text_input("💬 Your message:", placeholder="Type your message here...")
        submit_text = "Send"
    submitted = st.form_submit_button(submit_text)

if submitted:
    if len(query.split()) >= 3:
        # Choix du message de spinner sans backslash
        spinner_msg = (
            "💡 Assistant is thinking..."
            if st.session_state.lang == "en"
            else "💡 L'assistant réfléchit..."
        )
        with st.spinner(spinner_msg):
            search_results = search_faiss(query, top_n=5)
            faiss_context = "\n".join([doc for doc, _ in search_results])
            memory_context = "\n".join(st.session_state.chat_memory.get_context())
            full_context = f"{memory_context}\n\n{faiss_context}"
            response = get_answer(query, full_context)

            # Ajouter à l'historique
            st.session_state.chat_memory.add_to_memory(query, response)

            # Animation GPT tape…
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
                    """,
                    unsafe_allow_html=True,
                )
                time.sleep(0.01)

        # Mise à jour de la page
        st.rerun()
    else:
        warning_text = (
            "Please enter a question with at least three words."
            if st.session_state.lang == "en"
            else "Veuillez entrer une question avec au moins trois mots."
        )
        st.warning(warning_text)

# Bouton pour effacer la conversation
clear_text = "🧹 Clear conversation" if st.session_state.lang=='en' else "🧹 Effacer toute la conversation"
if st.button(clear_text):
    st.session_state.chat_memory.clear_memory()
    st.experimental_rerun()
