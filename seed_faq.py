import boto3
import os
from dotenv import load_dotenv

load_dotenv()

boto_args = {
    'region_name': os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
    'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
    'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY')
}

dynamodb = boto3.resource('dynamodb', **boto_args)
table_name = os.getenv('DYNAMODB_TABLE_FAQ', 'TazasFAQ')

def seed_faq():
    table = dynamodb.Table(table_name)
    
    faqs = [
        {
            'id': 'FAQ-001',
            'pregunta': '¿Cuáles son los días de entrega?',
            'respuesta': 'Realizamos entregas únicamente los días Miércoles y Sábados.'
        },
        {
            'id': 'FAQ-002',
            'pregunta': '¿En qué horario entregan los pedidos?',
            'respuesta': 'El horario de entrega es de 10:00 AM a 6:00 PM.'
        },
        {
            'id': 'FAQ-003',
            'pregunta': '¿Aceptan pagos contra entrega?',
            'respuesta': 'No, somos una tienda 100% online. Todos los pedidos requieren un 50% de adelanto para iniciar producción.'
        },
        {
            'id': 'FAQ-004',
            'pregunta': '¿Por qué medios puedo pagar?',
            'respuesta': 'Aceptamos pagos por Yape, Plin y transferencia al BCP.'
        },
        {
            'id': 'FAQ-005',
            'pregunta': '¿Hacen envíos a provincia?',
            'respuesta': 'Sí, realizamos envíos a todo el Perú a través de Olva Courier. El costo de envío se paga en destino.'
        },
        {
            'id': 'FAQ-006',
            'pregunta': '¿Cuánto tiempo tarda la producción de una taza personalizada?',
            'respuesta': 'La producción toma de 2 a 3 días hábiles una vez confirmado el diseño y realizado el adelanto.'
        },
        {
            'id': 'FAQ-007',
            'pregunta': '¿Qué pasa si la taza llega rota?',
            'respuesta': 'Si tu pedido llega dañado, tienes un máximo de 24 horas para enviarnos fotos del paquete y procederemos con el reemplazo sin costo adicional.'
        },
        {
            'id': 'FAQ-008',
            'pregunta': '¿Tienen tienda física?',
            'respuesta': 'No contamos con tienda física. Toda nuestra operación es 100% virtual.'
        },
        {
            'id': 'FAQ-009',
            'pregunta': '¿Puedo cancelar mi pedido y pedir reembolso?',
            'respuesta': 'Solo se pueden cancelar pedidos si aún no han entrado a producción (primeras 12 horas). Si ya se empezó a fabricar el diseño personalizado, no hay reembolsos.'
        },
        {
            'id': 'FAQ-010',
            'pregunta': '¿Qué características tiene la taza mágica?',
            'respuesta': 'La taza mágica es de color oscuro cuando está fría. Al verter líquido caliente, revela gradualmente el diseño impreso.'
        },
        {
            'id': 'FAQ-011',
            'pregunta': '¿Los diseños pueden incluir fotos?',
            'respuesta': 'Sí, podemos imprimir fotos, textos, logos o cualquier diseño sin costo adicional, siempre que nos envíes la imagen en buena calidad.'
        }
    ]
    
    print(f"Insertando {len(faqs)} FAQs en la tabla {table_name}...")
    for item in faqs:
        table.put_item(Item=item)
        print(f"Insertado: {item['id']}")

if __name__ == "__main__":
    try:
        dynamodb.meta.client.describe_table(TableName=table_name)
    except Exception as e:
        print(f"La tabla {table_name} no existe. Creando tabla...")
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print("Tabla creada.")
        
    seed_faq()
