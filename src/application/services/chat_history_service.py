"""
Servicio de historial de chat.
Formatea los mensajes de LangGraph a un formato legible para el frontend.
"""
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


def format_chat_history(messages: list) -> list[dict]:
    """
    Convierte una lista de mensajes de LangGraph (HumanMessage, AIMessage, ToolMessage)
    en una lista de dicts {sender, text} para el frontend.
    """
    formatted: list[dict] = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            formatted.append({"sender": "user", "text": msg.content})
        elif isinstance(msg, AIMessage):
            # Split by ||| to match WhatsApp's separate messages
            parts = msg.content.split("|||")
            for part in parts:
                part = part.strip()
                if part:
                    formatted.append({"sender": "bot", "text": part})
        elif isinstance(msg, ToolMessage):
            # Los ToolMessages son internos; no se muestran al usuario
            pass
    return formatted
