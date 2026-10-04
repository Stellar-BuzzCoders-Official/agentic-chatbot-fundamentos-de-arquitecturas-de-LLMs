"""
Schemas (modelos Pydantic) para los endpoints del Admin Dashboard.
"""
from pydantic import BaseModel


class StatusUpdate(BaseModel):
    """Payload para cambiar el estado del bot (bot_active | human_handoff)."""
    status: str


class AdminMessage(BaseModel):
    """Payload para enviar un mensaje manual desde el dashboard."""
    message: str


class SendMessageRequest(BaseModel):
    """Payload para el endpoint manual de envío a WhatsApp."""
    to_number: str
    message: str


class ChatRequest(BaseModel):
    """Payload para probar el bot desde Postman o Swagger sin necesidad de Meta."""
    message: str
    thread_id: str = "test_user_1"
