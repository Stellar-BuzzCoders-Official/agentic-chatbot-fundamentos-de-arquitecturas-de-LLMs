import boto3
import time
from typing import List, Dict, Optional
from src.providers.config import get_settings


class ContactsAdapter:
    def __init__(self):
        self.settings = get_settings()
        boto_args = {
            'region_name': self.settings.aws_default_region,
            'aws_access_key_id': self.settings.aws_access_key_id,
            'aws_secret_access_key': self.settings.aws_secret_access_key
        }

        if self.settings.dynamodb_local_endpoint:
            boto_args['endpoint_url'] = self.settings.dynamodb_local_endpoint

        self.dynamodb = boto3.resource('dynamodb', **boto_args)
        self.contacts_table = self.dynamodb.Table(
            self.settings.dynamodb_table_contacts)

    def upsert_contact(self, phone_number: str, profile_name: str = "Desconocido") -> None:
        """
        Guarda o actualiza un contacto. 
        Si el contacto ya existe, solo actualiza su timestamp y nombre.
        Si no, lo crea con status = 'bot_active'.
        """
        try:
            current_time = str(int(time.time()))
            # Utilizamos UpdateItem para hacer un upsert
            self.contacts_table.update_item(
                Key={'phone_number': phone_number},
                UpdateExpression="SET last_active = :time, profile_name = :profile_name, bot_status = if_not_exists(bot_status, :bot_active)",
                ExpressionAttributeValues={
                    ':time': current_time,
                    ':profile_name': profile_name,
                    ':bot_active': 'bot_active'
                }
            )
        except Exception as e:
            print(f"Error upserting contact {phone_number}: {e}")

    def update_bot_status(self, phone_number: str, status: str) -> None:
        """
        Actualiza el estado del bot ('bot_active' o 'human_handoff').
        """
        try:
            self.contacts_table.update_item(
                Key={'phone_number': phone_number},
                UpdateExpression="SET bot_status = :status",
                ExpressionAttributeValues={
                    ':status': status
                }
            )
        except Exception as e:
            print(f"Error updating bot status for {phone_number}: {e}")

    def update_terms_accepted(self, phone_number: str, accepted: bool) -> None:
        """
        Marca si el contacto aceptó o rechazó los Términos y Condiciones.
        """
        try:
            self.contacts_table.update_item(
                Key={'phone_number': phone_number},
                UpdateExpression="SET terms_accepted = :accepted",
                ExpressionAttributeValues={
                    ':accepted': accepted
                }
            )
        except Exception as e:
            print(f"Error updating terms_accepted for {phone_number}: {e}")

    def reset_terms(self, phone_number: str) -> None:
        """
        Elimina el registro de aceptación de T&C para pedirlo de nuevo en la siguiente conversación.
        """
        try:
            self.contacts_table.update_item(
                Key={'phone_number': phone_number},
                UpdateExpression="REMOVE terms_accepted"
            )
        except Exception as e:
            print(f"Error resetting terms_accepted for {phone_number}: {e}")

    def get_contact(self, phone_number: str) -> Optional[Dict]:
        try:
            response = self.contacts_table.get_item(
                Key={'phone_number': phone_number})
            return response.get('Item')
        except Exception as e:
            print(f"Error fetching contact {phone_number}: {e}")
            return None

    def get_all_contacts(self) -> List[Dict]:
        try:
            response = self.contacts_table.scan()
            items = response.get('Items', [])
            # Sort by last_active descending (assuming it's a string representing a timestamp)
            items.sort(key=lambda x: x.get('last_active', '0'), reverse=True)
            return items
        except Exception as e:
            print(f"Error fetching all contacts: {e}")
            return []
