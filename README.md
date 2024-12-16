# Chatbot d'extraction de texte PDF

Ce projet est un chatbot utilisant l’API Google Gemini pour répondre à des questions contextuelles basées sur du texte extrait de fichiers PDF.

## Installation

1. **Configuration de l'environnement :**
   Créez un fichier `.env` contenant votre clé API :
   GEMINI_API_KEY=Votre_Cle_Gemini

2. **Créer l’environnement virtuel et installer les dépendances :**
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
python -m venv fid_env
.\fid_env\Scripts\activate
python.exe -m pip install --upgrade pip
pip install -r requirements.txt

**Utilisation**
Lancez l'application Streamlit :
streamlit run app.py

### Fonctionnement du Programme

1. **Première exécution** : Lors de la première exécution, le programme extrait le texte des fichiers PDF dans `pdf_files/` et enregistre chaque texte dans un fichier Excel dans `output/excel/`. Ce texte est prêt pour les futures consultations.
  
2. **Consultation rapide** : Lors des exécutions suivantes, le programme lit directement le texte stocké dans les fichiers Excel, économisant ainsi du temps de traitement.
  
3. **Question/Réponse** : L’utilisateur sélectionne un fichier PDF et pose une question. Le programme extrait le contexte pertinent du texte, puis utilise l’API Gemini pour générer une réponse.

### Résumé

Cette structure répond au besoin d’un chatbot efficace qui analyse des PDF et retient le contexte pertinent pour les réponses. Il évite la ré-extraction en s’appuyant sur le texte stocké. Assurez-vous que les dossiers `pdf_files`, `output/excel`, et `.env` sont configurés avant de lancer l’application.

### Structure du programme

fid/
├── pdf_files/                      # Contient les fichiers PDF à traiter
├── output/                         # Dossier pour les résultats traités
│   ├── excel/                      # Fichiers Excel générés
│   ├── json/                       # Fichiers JSON générés
├── css/                            # Dossier pour les fichiers CSS
│   └── styles.css                  # Feuille de style pour Streamlit
├── chatbot/                        # Dossier contenant les scripts du chatbot
│   ├── _init_.py                 # Initialisation du module chatbot
│   ├── extraction.py               # Extraction et structuration du texte PDF
│   ├── chat.py                     # Gestion du chatbot
│   ├── utils.py                    # Fonctions utilitaires
│   ├── config.py                   # Configuration des clés API et constantes
│   ├── context_filter.py           # Filtrage du contexte pertinent
│   ├── rag_pipeline.py             # Pipeline pour la logique RAG
│   ├── memory.py                   # Gestion de la mémoire conversationnelle
├── init_index.py                   # Script principal pour indexer les données
├── app.py                          # Application Streamlit principale
├── requirements.txt                # Fichier des dépendances
├── .env                            # Stockage des clés API
└── README.md                       # Documentation du projet
