# chatbot/chat.py
from chatbot.rag_pipeline import get_answer

def ask_question(question):
    """
    Pose une question et utilise RAG pour obtenir une réponse.
    """
    return get_answer(question)
