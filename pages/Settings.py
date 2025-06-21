# pages/Settings.py
import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Paramètres", page_icon="⚙️")

# Appliquer le thème actuel (pour le background)
theme = st.session_state.get("theme", "light")
st.markdown(f"<body data-theme='{theme}'>", unsafe_allow_html=True)

# Titre de la page
if st.session_state.lang == "fr":
    st.header("⚙️ Paramètres")
else:
    st.header("⚙️ Settings")

# Choix du thème (clair/sombre)
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if st.session_state.lang == "fr":
    theme_label = "Thème de l'application"
    theme_options = ["Clair", "Sombre"]
else:
    theme_label = "Application Theme"
    theme_options = ["Light", "Dark"]

current_theme = st.session_state.theme
index = 0 if current_theme == "light" else 1
theme_choice = st.radio(theme_label, theme_options, index=index)
st.session_state.theme = "light" if theme_choice in ["Clair", "Light"] else "dark"

# Choix de la langue
if "lang" not in st.session_state:
    st.session_state.lang = "fr"
lang_label = "Langue" if st.session_state.lang=="fr" else "Language"
lang_options = ["Français", "English"]
current_lang = st.session_state.lang
index = 0 if current_lang == "fr" else 1
lang_choice = st.selectbox(lang_label, lang_options, index=index)
st.session_state.lang = "fr" if lang_choice == "Français" else "en"
