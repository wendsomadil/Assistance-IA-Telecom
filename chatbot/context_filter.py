# chatbot/context_filter.py
def filter_context(question, texts):
    for file, content in texts.items():
        # Vérifier que le contenu n'est pas None avant d'appliquer .lower()
        if content and question.lower() in content.lower():
            return content
    return "Information non trouvée."
