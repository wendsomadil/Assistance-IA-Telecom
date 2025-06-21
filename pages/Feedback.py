# pages/Feedback.py
import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText

# Configuration de la page
st.set_page_config(page_title="Feedback", page_icon="💬")

# Appliquer le thème
theme = st.session_state.get("theme", "light")
st.markdown(f"<body data-theme='{theme}'>", unsafe_allow_html=True)

# Titre de la page
if st.session_state.lang == "fr":
    st.header("📝 Donnez votre avis")
else:
    st.header("📝 Give your feedback")

# Champs du formulaire
if st.session_state.lang == "fr":
    satisfaction = st.slider("Satisfaction (1 = Pas du tout, 5 = Très satisfait)", 1, 5, 3)
    feedback_text = st.text_area("Commentaire libre")
    send_button = st.button("📨 Envoyer le feedback")
else:
    satisfaction = st.slider("Satisfaction (1 = Not at all satisfied, 5 = Very satisfied)", 1, 5, 3)
    feedback_text = st.text_area("Your comments")
    send_button = st.button("📨 Send Feedback")

# Fonction d’envoi d’email
def envoyer_email(satisfaction, feedback):
    expediteur = "monappfeedback@gmail.com"
    mot_de_passe = "mill vwph cnue idej"
    destinataire = "wendsomadil@gmail.com"
    msg = MIMEText(f"Satisfaction: {satisfaction}/5\nCommentaire: {feedback}")
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
        return False

# Traitement à l'envoi
if send_button:
    # Sauvegarde locale
    df = pd.DataFrame({'satisfaction': [satisfaction], 'feedback': [feedback_text]})
    df.to_csv('feedback.csv', mode='a', header=False, index=False)
    # Envoi email
    if envoyer_email(satisfaction, feedback_text):
        msg = "Merci pour votre retour !" if st.session_state.lang=='fr' else "Thank you for your feedback!"
        st.success(msg)
    else:
        error_msg = "Échec lors de l'envoi de l'email." if st.session_state.lang=='fr' else "Failed to send email."
        st.error(error_msg)
