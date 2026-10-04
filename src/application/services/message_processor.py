"""
Módulo de procesamiento de mensajes entrantes de WhatsApp.
Contiene la lógica del pipeline: orquestador → respuesta → envío → recordatorios.
"""
import asyncio
from src.application.services.chatbot_orchestrator import ChatbotOrchestrator
from src.infrastructure.output.whatsapp_api import (
    send_whatsapp_message,
    send_whatsapp_typing,
    send_whatsapp_interactive_terms,
    send_whatsapp_image
)
import re
from src.providers.config import get_settings
from src.infrastructure.output.contacts_adapter import ContactsAdapter
from src.infrastructure.input.websocket_manager import ws_manager
from langchain_core.messages import HumanMessage

settings = get_settings()

contacts_adapter = ContactsAdapter()

# Instancia global del orquestador
orchestrator = ChatbotOrchestrator()

# Almacena tareas activas de timeout por número
active_reminders: dict[str, asyncio.Task] = {}

# Almacena el último wamid recibido por cada número para enviar typing indicators
last_incoming_wamid: dict[str, str] = {}


async def schedule_reminders(phone_number: str, phone_number_id: str):
    """Programa recordatorios automáticos si el usuario no responde."""

    async def send_and_broadcast(text: str):
        send_whatsapp_message(phone_number_id, phone_number, text)
        await ws_manager.broadcast({
            "type": "NEW_MESSAGE",
            "phone_number": phone_number,
            "message": {"sender": "bot", "text": text}
        })

    try:
        print(f"[REMINDER] Programado para {phone_number} — esperando 10 minutos (primer recordatorio)")
        # 10 minutes reminder
        await asyncio.sleep(600)
        contact = contacts_adapter.get_contact(phone_number)
        if not contact or contact.get('bot_status') != 'bot_active':
            print(f"[REMINDER] Abortado para {phone_number} — contact={contact}")
            return

        print(f"[REMINDER] Enviando primer recordatorio a {phone_number}")
        await send_and_broadcast("¡Hola! 😊 ¿Aún sigues por ahí? Recuerda que sigo aquí si tienes dudas sobre nuestras tazas.")

        print(f"[REMINDER] Esperando 50 minutos (segundo recordatorio) para {phone_number}")
        # 50 minutes more (total 1 hour)
        await asyncio.sleep(3000)
        contact = contacts_adapter.get_contact(phone_number)
        if not contact or contact.get('bot_status') != 'bot_active':
            print(f"[REMINDER] Abortado para {phone_number} — contact={contact}")
            return

        print(f"[REMINDER] Enviando segundo recordatorio a {phone_number}")
        await send_and_broadcast("¡Aún sigo por aquí! 😉 Avísame cuando quieras continuar.")

        print(f"[REMINDER] Esperando 3 horas (tercer recordatorio) para {phone_number}")
        # 3 hours more (total 4 hours)
        await asyncio.sleep(10800)
        contact = contacts_adapter.get_contact(phone_number)
        if not contact or contact.get('bot_status') != 'bot_active':
            print(f"[REMINDER] Abortado para {phone_number} — contact={contact}")
            return

        print(f"[REMINDER] Enviando tercer recordatorio (cierre) a {phone_number}")
        await send_and_broadcast(
            "Parece que te tuviste que ir. 😅 Estaré cerrando esta sesión por ahora, "
            "pero cuando quieras una taza genial, ¡solo escríbeme de nuevo! 👋"
        )


        # Cierre automático de chat
        orchestrator.saver.delete_thread(phone_number)
        await ws_manager.broadcast({"type": "CHAT_CLOSED", "phone_number": phone_number})

    except asyncio.CancelledError:
        pass
    finally:
        if active_reminders.get(phone_number) == asyncio.current_task():
            del active_reminders[phone_number]


async def process_whatsapp_message(
    phone_number: str,
    text: str,
    phone_number_id: str,
    bot_status: str,
    msg_id: str = None,
):
    """Pipeline principal: recibe un mensaje, lo procesa con el orquestador y envía la respuesta."""

    # Cancel previous reminder task if exists
    if phone_number in active_reminders:
        active_reminders[phone_number].cancel()

    # Broadcast incoming message to dashboard
    await ws_manager.broadcast({
        "type": "NEW_MESSAGE",
        "phone_number": phone_number,
        "message": {"sender": "user", "text": text},
    })

    # Si está en modo humano, ignoramos el flujo del bot
    if bot_status == "human_handoff":
        print(f"[{phone_number}] Bot pausado. Mensaje ignorado: {text}")
        config = {"configurable": {"thread_id": phone_number}}
        orchestrator.app.update_state(config, {"messages": [HumanMessage(content=text)]})
        return

    contact = contacts_adapter.get_contact(phone_number)
    terms_accepted = contact.get("terms_accepted") if contact else None

    # Manejar respuestas a botones de T&C
    if text == "accept_terms":
        contacts_adapter.update_terms_accepted(phone_number, True)
        # Confirmamos al usuario y seguimos el flujo normal con un texto base para el agente
        text = "¡Excelente! He aceptado los Términos y Condiciones. ¿En qué me puedes ayudar?"
        terms_accepted = True
    elif text == "reject_terms":
        contacts_adapter.update_terms_accepted(phone_number, False)
        contacts_adapter.update_bot_status(phone_number, "human_handoff")
        bot_status = "human_handoff"
        await ws_manager.broadcast({
            "type": "CONTACT_UPDATED",
            "phone_number": phone_number,
            "bot_status": "human_handoff",
        })
        msg = "Entendido. No podemos continuar automáticamente, pero te derivaremos con un asesor humano para que te ayude."
        send_whatsapp_message(phone_number_id, phone_number, msg)
        await ws_manager.broadcast({
            "type": "NEW_MESSAGE",
            "phone_number": phone_number,
            "message": {"sender": "bot", "text": msg}
        })
        return

    # Si aún no ha aceptado ni rechazado, le forzamos a hacerlo
    if terms_accepted is None:
        # Enviar mensaje de bienvenida genérico + Botonera de Términos
        welcome_text = "¡Hola! 😊 Soy el asistente virtual de **Khronos**, tu tienda 100% online de tazas personalizadas."
        send_whatsapp_message(phone_number_id, phone_number, welcome_text)
        send_whatsapp_interactive_terms(
            phone_number_id,
            phone_number,
            "Para poder ayudarte a elegir o diseñar tu taza, primero necesitamos que aceptes nuestros Términos y Condiciones."
        )
        return
    elif terms_accepted is False:
        # Ya rechazó antes y está en human_handoff (cubierto arriba, pero por si acaso)
        return

    # Notificar que el bot está escribiendo (frontend)
    await ws_manager.broadcast({"type": "TYPING", "phone_number": phone_number})

    # Notificar que el bot está escribiendo (WhatsApp API) si tenemos un msg_id
    if msg_id and phone_number_id:
        send_whatsapp_typing(phone_number_id, msg_id)

    # Invocamos a nuestro orquestador ReAct de forma asíncrona
    response_text, request_handoff = await orchestrator.ainvoke(text, thread_id=phone_number)

    # Si el agente determinó que debe haber un desvío (handoff) a humano
    if request_handoff:
        contacts_adapter.update_bot_status(phone_number, "human_handoff")
        bot_status = "human_handoff"
        await ws_manager.broadcast({
            "type": "CONTACT_UPDATED",
            "phone_number": phone_number,
            "bot_status": "human_handoff",
        })

    # (ya no usamos la tool de T&C dinámica, removemos "[TERMS_BUTTON]" si por error apareciera)
    response_text = response_text.replace("[TERMS_BUTTON]", "").strip()

    # Enviar la respuesta a través de Meta API
    if phone_number_id and settings.whatsapp_token:
        parts = response_text.split("|||")
        for i, part in enumerate(parts):
            part = part.strip()
            wa_part = part.replace("**", "*")

            if wa_part:
                # Buscar si el mensaje contiene una URL de imagen
                url_match = re.search(r"(https?://\S+\.(?:jpg|jpeg|png))", wa_part, re.IGNORECASE)
                
                if url_match:
                    image_url = url_match.group(1)
                    # Remover la URL y la palabra 'Imagen:' si existe, para usar el resto como caption
                    clean_text = re.sub(r"Imagen:\s*" + re.escape(image_url), "", wa_part, flags=re.IGNORECASE)
                    clean_text = clean_text.replace(image_url, "").strip()
                    
                    send_whatsapp_image(phone_number_id, phone_number, image_url, caption=clean_text)
                    
                    # Actualizar dashboard
                    await ws_manager.broadcast({
                        "type": "NEW_MESSAGE",
                        "phone_number": phone_number,
                        "message": {"sender": "bot", "text": f"[Imagen enviada] {clean_text}"},
                    })
                else:
                    send_whatsapp_message(phone_number_id, phone_number, wa_part)
                    
                    await ws_manager.broadcast({
                        "type": "NEW_MESSAGE",
                        "phone_number": phone_number,
                        "message": {"sender": "bot", "text": wa_part},
                    })

                if i < len(parts) - 1:
                    await ws_manager.broadcast({"type": "TYPING", "phone_number": phone_number})
                    if msg_id and phone_number_id:
                        send_whatsapp_typing(phone_number_id, msg_id)

                    next_len = len(parts[i + 1].strip())
                    delay = max(2.5, min(next_len * 0.05, 5.0))
                    await asyncio.sleep(delay)

    print(f"Respuesta enviada a {phone_number}: {response_text}")

    # Reiniciar temporizadores de recordatorio (solo si está en modo bot)
    if bot_status == "bot_active":

        loop = asyncio.get_running_loop()
        active_reminders[phone_number] = loop.create_task(
            schedule_reminders(phone_number, phone_number_id)
        )
