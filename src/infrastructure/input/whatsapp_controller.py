"""
Controller de WhatsApp – Solo endpoints HTTP.
La lógica de procesamiento de mensajes está en message_processor.py
y la comunicación con la Graph API está en whatsapp_api.py.
"""
from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from src.infrastructure.input.schemas import SendMessageRequest, ChatRequest
from src.providers.config import get_settings
from src.application.services.message_processor import (
    orchestrator,
    process_whatsapp_message,
    last_incoming_wamid,
    active_reminders,
)
from src.infrastructure.output.whatsapp_api import (
    send_whatsapp_message,
    send_whatsapp_typing,
)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
settings = get_settings()

from src.infrastructure.output.contacts_adapter import ContactsAdapter
contacts_adapter = ContactsAdapter()


# ──────────────────────────────────────────────
#  Webhook de Meta WhatsApp Cloud API
# ──────────────────────────────────────────────

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Endpoint para verificación de Meta WhatsApp Cloud API."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Token de verificación inválido")


@router.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    """Endpoint para recibir mensajes de WhatsApp Cloud API."""
    body = await request.json()
    print("--- WEBHOOK RECIBIDO ---")

    if body.get("object") == "whatsapp_business_account":
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                metadata = value.get("metadata", {})
                contacts_info = value.get("contacts", [])

                if messages:
                    msg = messages[0]
                    msg_type = msg.get("type")
                    phone_number = msg.get("from")
                    phone_number_id = metadata.get("phone_number_id")
                    msg_id = msg.get("id")

                    profile_name = "Desconocido"
                    if contacts_info and len(contacts_info) > 0:
                        profile_name = contacts_info[0].get("profile", {}).get("name", "Desconocido")

                    text = _extract_text_from_message(msg, msg_type)

                    if text and phone_number:
                        contact = contacts_adapter.get_contact(phone_number)
                        bot_status = contact.get("bot_status") if contact else "bot_active"

                        contacts_adapter.upsert_contact(phone_number, profile_name)

                        if msg_id:
                            last_incoming_wamid[phone_number] = msg_id

                        background_tasks.add_task(
                            process_whatsapp_message,
                            phone_number,
                            text,
                            phone_number_id,
                            bot_status,
                            msg_id,
                        )

        return {"status": "ok"}

    raise HTTPException(status_code=400, detail="Estructura no válida")


# ──────────────────────────────────────────────
#  Endpoints auxiliares
# ──────────────────────────────────────────────

@router.post("/send")
async def api_send_message(req: SendMessageRequest):
    """Endpoint manual para enviar un mensaje a un número de WhatsApp."""
    phone_id = settings.whatsapp_phone_number_id
    if not phone_id:
        raise HTTPException(status_code=400, detail="Falta el phone_number_id. Configúralo en el .env")

    result = send_whatsapp_message(phone_id, req.to_number, req.message)
    return {"status": "sent", "meta_response": result}


@router.post("/chat-local")
async def local_chat(req: ChatRequest):
    """Endpoint para probar el bot desde Postman o Swagger sin necesidad de Meta."""
    response, request_handoff = orchestrator.invoke(req.message, thread_id=req.thread_id)
    return {
        "message_received": req.message,
        "response": response,
        "request_handoff": request_handoff,
        "thread_id": req.thread_id,
    }


@router.delete("/history/{phone_number}")
async def clear_history(phone_number: str):
    """Endpoint para eliminar el historial de conversación de un número específico y reiniciar TyC."""
    try:
        orchestrator.saver.delete_thread(phone_number)
        contacts_adapter.reset_terms(phone_number)
        return {"status": "success", "message": f"Historial eliminado correctamente para el número {phone_number}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
#  Helpers privados
# ──────────────────────────────────────────────

def _extract_text_from_message(msg: dict, msg_type: str) -> str | None:
    """Extrae el texto relevante de un mensaje según su tipo."""
    if msg_type == "text":
        return msg.get("text", {}).get("body", "")
    elif msg_type == "image":
        caption = msg.get("image", {}).get("caption", "")
        return f"[📷 Imagen recibida]{' - ' + caption if caption else ''}"
    elif msg_type == "document":
        filename = msg.get("document", {}).get("filename", "archivo")
        return f"[📎 Documento recibido: {filename}]"
    elif msg_type == "audio":
        return "[🎤 Audio recibido]"
    elif msg_type == "sticker":
        return "[🎨 Sticker recibido]"
    elif msg_type == "video":
        return "[🎬 Video recibido]"
    elif msg_type == "interactive":
        interactive = msg.get("interactive", {})
        if interactive.get("type") == "button_reply":
            return interactive.get("button_reply", {}).get("id", "")
    return None
