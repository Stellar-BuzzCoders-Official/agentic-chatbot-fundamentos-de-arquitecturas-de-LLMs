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
def check_inventory(query: str = "") -> str:
    """Consulta el catálogo de tazas personalizadas. Usa esta herramienta para buscar productos, precios y características."""
    try:
        table = dynamodb.Table(settings.dynamodb_table_products)
        response = table.scan()
        products = response.get('Items', [])
    except Exception as e:
        print(f"Error consultando DynamoDB para inventario: {e}")
        return "Actualmente no hay productos disponibles o hubo un error al consultar el catálogo."
    
    if not products:
        return "Actualmente no hay productos disponibles."
    
    catalog = "Catálogo de Tazas Disponibles:\n"
    for p in products:
        catalog += f"- {p.get('name')}: S/. {p.get('price')} (Capacidad: {p.get('capacity_oz')} oz)\n"
        if p.get('description'):
            catalog += f"  Descripción: {p.get('description')}\n"
        if p.get('colors'):
            catalog += f"  Colores disponibles: {', '.join(p.get('colors'))}\n"
        if p.get('image_url'):
            catalog += f"  Imagen: {p.get('image_url')}\n"
    
    return catalog
