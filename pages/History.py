# pages/History.py
import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Historique", page_icon="🕒")

# Appliquer le thème
theme = st.session_state.get("theme", "light")
st.markdown(f"<body data-theme='{theme}'>", unsafe_allow_html=True)

# Titre de la page
if st.session_state.lang == "fr":
    st.header("📜 Historique des messages")
else:
    st.header("📜 Conversation History")

# Vérifier s’il y a une mémoire de chat
history = st.session_state.chat_memory.history if "chat_memory" in st.session_state else []
if not history:
    info_text = ("Aucune conversation pour le moment." 
                 if st.session_state.lang=='en' else "Aucune conversation pour le moment.")
    st.info(info_text)
else:
    # Affichage numéroté des échanges
    for idx, message in enumerate(history, 1):
        if st.session_state.lang == "fr":
            vous_label = "**Vous:**"
            bot_label = "**Bot:**"
        else:
            vous_label = "**You:**"
            bot_label = "**Bot:**"
        st.markdown(f"{idx}. {vous_label} {message['user']}  \n   {bot_label} {message['bot']}")

# Bouton pour effacer l’historique
st.markdown("---")
clear_text = "🧹 Clear entire history" if st.session_state.lang=='en' else "🧹 Effacer toute la conversation"
if st.button(clear_text):
    st.session_state.chat_memory.clear_memory()
    st.experimental_rerun()
