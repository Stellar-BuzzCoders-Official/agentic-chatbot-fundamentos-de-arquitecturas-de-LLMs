"""
Controller del Admin Dashboard – Endpoints HTTP y WebSocket.
Los schemas están en schemas.py, la lógica de historial en chat_history_service.py,
y la comunicación con WhatsApp en whatsapp_api.py.
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from src.infrastructure.output.contacts_adapter import ContactsAdapter
from src.application.services.message_processor import orchestrator, active_reminders, last_incoming_wamid
from src.infrastructure.output.whatsapp_api import send_whatsapp_message, send_whatsapp_typing
from src.application.services.chat_history_service import format_chat_history
from src.infrastructure.input.websocket_manager import ws_manager
from src.infrastructure.input.schemas import StatusUpdate, AdminMessage
from src.providers.config import get_settings
from langchain_core.messages import AIMessage

router = APIRouter(prefix="/api/admin", tags=["Admin"])
contacts_adapter = ContactsAdapter()
settings = get_settings()


# ──────────────────────────────────────────────
#  WebSocket
# ──────────────────────────────────────────────

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Conexión WebSocket para comunicación en tiempo real con el dashboard."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ──────────────────────────────────────────────
#  Contactos
# ──────────────────────────────────────────────

@router.get("/contacts")
def get_contacts():
    """Lista todos los contactos que han interactuado."""
    contacts = contacts_adapter.get_all_contacts()
    return {"contacts": contacts}


# ──────────────────────────────────────────────
#  Chat
# ──────────────────────────────────────────────

@router.get("/chats/{phone_number}")
def get_chat_history(phone_number: str):
    """Obtiene el historial de chat de un número específico."""
    config = {"configurable": {"thread_id": phone_number}}
    state_snapshot = orchestrator.app.get_state(config)

    if not state_snapshot or not state_snapshot.values:
        return {"messages": []}

    messages = state_snapshot.values.get("messages", [])
    return {"messages": format_chat_history(messages)}


@router.post("/chats/{phone_number}/status")
async def update_chat_status(phone_number: str, payload: StatusUpdate):
    """Pausa (human_handoff) o reanuda (bot_active) el bot para un usuario."""
    if payload.status not in ["bot_active", "human_handoff"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    contacts_adapter.update_bot_status(phone_number, payload.status)

    await ws_manager.broadcast({
        "type": "CONTACT_UPDATED",
        "phone_number": phone_number,
        "bot_status": payload.status,
    })

    return {"status": "success", "new_status": payload.status}


@router.post("/chats/{phone_number}/send")
async def admin_send_message(phone_number: str, payload: AdminMessage):
    """Envía un mensaje manual desde el dashboard vía WhatsApp."""
    phone_id = settings.whatsapp_phone_number_id
    if not phone_id:
        raise HTTPException(status_code=500, detail="Falta whatsapp_phone_number_id")

    wa_message = payload.message.replace("**", "*")
    result = send_whatsapp_message(phone_id, phone_number, wa_message)

    # Registrar en la memoria de LangGraph
    config = {"configurable": {"thread_id": phone_number}}
    orchestrator.app.update_state(config, {"messages": [AIMessage(content=payload.message)]})

    contacts_adapter.upsert_contact(phone_number)

    await ws_manager.broadcast({
        "type": "NEW_MESSAGE",
        "phone_number": phone_number,
        "message": {"sender": "bot", "text": wa_message},
    })

    return {"status": "sent", "meta_response": result}


@router.post("/chats/{phone_number}/close")
async def close_chat(phone_number: str):
    """Cierra un chat manualmente, limpia la memoria y envía un mensaje de cierre."""
    phone_id = settings.whatsapp_phone_number_id
    if not phone_id:
        raise HTTPException(status_code=500, detail="Falta whatsapp_phone_number_id")

    closing_message = (
        "Esta conversación ha sido cerrada por un administrador. "
        "Si tienes más consultas, no dudes en escribirnos de nuevo. ¡Gracias!"
    )

    result = send_whatsapp_message(phone_id, phone_number, closing_message)
    orchestrator.saver.delete_thread(phone_number)
    contacts_adapter.reset_terms(phone_number)
    contacts_adapter.update_bot_status(phone_number, "bot_active")

    if phone_number in active_reminders:
        active_reminders[phone_number].cancel()

    await ws_manager.broadcast({"type": "CHAT_CLOSED", "phone_number": phone_number})

    return {"status": "closed", "meta_response": result}


@router.post("/chats/{phone_number}/typing")
async def send_typing_indicator(phone_number: str):
    """Envía un indicador de 'escribiendo...' a WhatsApp desde el dashboard."""
    phone_id = settings.whatsapp_phone_number_id
    msg_id = last_incoming_wamid.get(phone_number)

    if msg_id and phone_id:
        send_whatsapp_typing(phone_id, msg_id)

    return {"status": "ok"}
