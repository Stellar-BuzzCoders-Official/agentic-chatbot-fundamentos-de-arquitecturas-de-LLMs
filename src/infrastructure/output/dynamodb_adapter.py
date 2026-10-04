import boto3
from typing import List, Optional
from src.providers.config import get_settings
from src.domain.models.product import Product

class DynamoDBAdapter:
    def __init__(self):
        self.settings = get_settings()
        boto_args = {
            'region_name': self.settings.aws_default_region,
            'aws_access_key_id': self.settings.aws_access_key_id,
            'aws_secret_access_key': self.settings.aws_secret_access_key
        }
        
        if self.settings.environment.lower() == "local":
            boto_args['endpoint_url'] = self.settings.dynamodb_local_endpoint

        self.dynamodb = boto3.resource('dynamodb', **boto_args)
        self.products_table = self.dynamodb.Table(self.settings.dynamodb_table_products)
        self.faq_table = self.dynamodb.Table(self.settings.dynamodb_table_faq)

    def get_all_products(self) -> List[Product]:
        try:
            response = self.products_table.scan()
            items = response.get('Items', [])
            products = []
            for item in items:
                products.append(
                    Product(
                        id=item.get('id', ''),
                        name=item.get('name', ''),
                        price=float(item.get('price', 0.0)),
                        description=item.get('description'),
                        colors=item.get('colors'),
                        capacity_oz=int(item.get('capacity_oz')) if item.get('capacity_oz') else None
                    )
                )
            return products
        except Exception as e:
            print(f"Error fetching products from DynamoDB: {e}")
            return []

    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        try:
            response = self.products_table.get_item(Key={'id': product_id})
            item = response.get('Item')
            if item:
                return Product(
                    id=item.get('id', ''),
                    name=item.get('name', ''),
                    price=float(item.get('price', 0.0)),
                    description=item.get('description'),
                    colors=item.get('colors'),
                    capacity_oz=int(item.get('capacity_oz')) if item.get('capacity_oz') else None
                )
            return None
        except Exception as e:
            print(f"Error fetching product {product_id}: {e}")
            return None
