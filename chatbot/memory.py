# chatbot.memory.py
"""
Module pour gérer la mémoire de la conversation (sauvegarde des questions/réponses).
"""

class ChatMemory:
    def __init__(self):
        """Initialise la mémoire avec un historique vide."""
        self.history = []

    def add_to_memory(self, user_input, bot_response):
        """Ajoute une paire question/réponse à l'historique."""
        self.history.append({"user": user_input, "bot": bot_response})

    def get_context(self, num_last_messages=3):
        """Récupère le contexte des derniers échanges."""
        context = []
        for item in self.history[-num_last_messages:]:
            context.append(f"User: {item['user']}\nBot: {item['bot']}")
        return context

    def clear_memory(self):
        """Vide l'historique de la mémoire."""
        self.history = []
