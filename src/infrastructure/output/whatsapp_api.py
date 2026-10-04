"""
Módulo de comunicación con la Graph API de WhatsApp (Meta).
Contiene todas las funciones de envío de mensajes, typing indicators y mensajes interactivos.
"""
import requests
from src.providers.config import get_settings

settings = get_settings()


def send_whatsapp_message(phone_number_id: str, to_number: str, text: str):
    """
    Envía un mensaje de texto simple a través de la Graph API de Meta.
    """
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "preview_url": True,
            "body": text
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


def send_whatsapp_typing(phone_number_id: str, msg_id: str):
    """
    Activa el indicador de 'escribiendo...' en WhatsApp marcando el último
    mensaje entrante como leído y enviando el typing_indicator.
    Nota: Desaparece cuando el bot envía un mensaje o después de 25 segundos.
    """
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": msg_id,
        "typing_indicator": {
            "type": "text"
        }
    }
    try:
        requests.post(url, headers=headers, json=payload, timeout=2)
    except:
        pass


def send_whatsapp_interactive_terms(phone_number_id: str, to_number: str, text: str):
    """
    Envía un mensaje interactivo con el botón de Términos y Condiciones.
    """
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json"
    }

    body_text = (
        text.strip()
        + "\n\n📄 Lee nuestros Términos y Condiciones aquí:\n"
        "https://tazas-admin-dashboard.onrender.com/terms\n\n"
        "Por favor, acepta los términos para continuar."
    )

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": body_text
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "accept_terms",
                            "title": "Si Acepto"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "reject_terms",
                            "title": "No acepto"
                        }
                    }
                ]
            }
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def send_whatsapp_image(phone_number_id: str, to_number: str, image_url: str, caption: str = ""):
    """
    Envía un mensaje de tipo imagen a través de la Graph API de Meta.
    """
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "image",
        "image": {
            "link": image_url
        }
    }
    if caption:
        payload["image"]["caption"] = caption

    response = requests.post(url, headers=headers, json=payload)
    return response.json()
