from langchain_core.tools import tool


@tool
def send_terms_and_conditions() -> str:
    """Envía al cliente los Términos y Condiciones de compra con un botón interactivo para que los acepte. Usa esta herramienta OBLIGATORIAMENTE en tu primer mensaje de cada conversación, justo después de presentarte."""
    return "[TERMS_BUTTON]"
