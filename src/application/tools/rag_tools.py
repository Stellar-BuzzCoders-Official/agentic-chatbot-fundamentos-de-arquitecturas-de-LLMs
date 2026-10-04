import boto3
from langchain_core.tools import tool
from src.providers.config import get_settings

settings = get_settings()

boto_args = {
    "aws_access_key_id": settings.aws_access_key_id,
    "aws_secret_access_key": settings.aws_secret_access_key,
    "region_name": settings.aws_default_region
}
if settings.environment.lower() == "local":
    boto_args["endpoint_url"] = settings.dynamodb_local_endpoint

dynamodb = boto3.resource("dynamodb", **boto_args)

@tool
def get_faq_and_policies(query: str = "") -> str:
    """Consulta esta herramienta para responder preguntas sobre envíos, métodos de pago, y tiempos de producción."""
    try:
        table = dynamodb.Table(settings.dynamodb_table_faq)
        response = table.scan()
        faqs = response.get('Items', [])
    except Exception as e:
        print(f"Error consultando DynamoDB para FAQ: {e}")
        return "Actualmente no tengo información de políticas y envío."
        
    if not faqs:
        return "Actualmente no hay políticas registradas."
        
    faq_text = "Políticas y Preguntas Frecuentes:\n"
    for item in faqs:
        faq_text += f"P: {item.get('pregunta')}\nR: {item.get('respuesta')}\n\n"
        
    return faq_text
