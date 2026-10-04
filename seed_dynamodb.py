import boto3
import os
from decimal import Decimal
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configurar boto3 usando las variables de entorno
boto_args = {
    'region_name': os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
    'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
    'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY')
}

if os.getenv("ENVIRONMENT", "").lower() == "local":
    boto_args["endpoint_url"] = os.getenv("DYNAMODB_LOCAL_ENDPOINT", "http://localhost:8000")

dynamodb = boto3.resource('dynamodb', **boto_args)
table_name = os.getenv('DYNAMODB_TABLE_PRODUCTS', 'TazasProducts')

def create_table_if_not_exists():
    try:
        # Intenta describir la tabla para ver si existe
        dynamodb.meta.client.describe_table(TableName=table_name)
        print(f"La tabla {table_name} ya existe. Procediendo a insertar datos...")
    except dynamodb.meta.client.exceptions.ResourceNotFoundException:
        print(f"La tabla {table_name} no existe. Creándola ahora...")
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        # Esperar a que la tabla se cree
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print(f"Tabla {table_name} creada exitosamente.")

def seed_products():
    table = dynamodb.Table(table_name)
    
    products = [
        {
            'id': 'PROD-001',
            'name': 'TAZA DE 15 OZ 3A SELLO NEGRO',
            'price': Decimal('11.00'),
            'capacity_oz': 15,
            'description': 'Taza clásica de 15 onzas, sello negro.'
        },
        {
            'id': 'PROD-002',
            'name': 'TAZA MAGICA DE 15 oz BRILLANTE',
            'price': Decimal('17.00'),
            'capacity_oz': 15,
            'description': 'Taza mágica que revela el diseño con líquidos calientes.'
        },
        {
            'id': 'PROD-003',
            'name': 'TAZA MAGICA DE 11 oz ASA CORAZON BRILLANTE',
            'price': Decimal('14.50'),
            'capacity_oz': 11,
            'description': 'Taza mágica con asa en forma de corazón.'
        },
        {
            'id': 'PROD-004',
            'name': 'TAZA 3D MAGICA BRILLANTE DE 11 OZ',
            'price': Decimal('18.50'),
            'capacity_oz': 11,
            'description': 'Taza mágica con efecto 3D.'
        },
        {
            'id': 'PROD-005',
            'name': 'TAZA ASA CUCHARA 12 OZ',
            'price': Decimal('15.00'),
            'capacity_oz': 12,
            'colors': ['Rojo', 'Rosa'],
            'description': 'Taza que incluye una cuchara en el asa.'
        },
        {
            'id': 'PROD-006',
            'name': 'TAZA BLANCA ASA Y FONDO DE COLOR 11 OZ',
            'price': Decimal('12.00'),
            'capacity_oz': 11,
            'colors': ['Rojo', 'Rosa', 'Verde', 'Azul', 'Celeste', 'Negro'],
            'description': 'Taza blanca con el asa y el interior de color.'
        },
        {
            'id': 'PROD-007',
            'name': 'TAZA BLANCA ASA CORAZON ASA Y FONDO DE COLOR',
            'price': Decimal('14.00'),
            'capacity_oz': 11,
            'description': 'Taza blanca con asa de corazón y fondo de color.'
        },
        {
            'id': 'PROD-008',
            'name': 'TUMBLERS DE 20 OZ',
            'price': Decimal('30.00'),
            'capacity_oz': 20,
            'description': 'Tumbler térmico para bebidas frías o calientes.'
        },
        {
            'id': 'PROD-009',
            'name': 'MUG DE ACERO COLOR BLANCO',
            'price': Decimal('28.00'),
            'description': 'Mug resistente de acero en color blanco.'
        }
    ]
    
    print(f"Insertando productos en la tabla {table_name}...")
    for p in products:
        table.put_item(Item=p)
        print(f"Insertado: {p['name']}")

if __name__ == "__main__":
    create_table_if_not_exists()
    seed_products()
