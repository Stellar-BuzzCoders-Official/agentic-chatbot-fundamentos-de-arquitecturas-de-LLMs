import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def create_memory_table():
    boto_args = {
        "region_name": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    }
    
    if os.getenv("ENVIRONMENT", "").lower() == "local":
        boto_args["endpoint_url"] = os.getenv("DYNAMODB_LOCAL_ENDPOINT", "http://localhost:8000")

    dynamodb = boto3.client("dynamodb", **boto_args)

    table_name = os.getenv("DYNAMODB_TABLE_MEMORY", "TazasChatHistory")

    try:
        existing_tables = dynamodb.list_tables()["TableNames"]
        if table_name not in existing_tables:
            print(f"Creating table '{table_name}'...")
            dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "PK", "KeyType": "HASH"},
                    {"AttributeName": "SK", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "PK", "AttributeType": "S"},
                    {"AttributeName": "SK", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            print(f"Table '{table_name}' creation requested. Waiting for it to become active...")
            dynamodb.get_waiter('table_exists').wait(TableName=table_name)
            print(f"Table '{table_name}' is now active and ready to use.")
        else:
            print(f"Table '{table_name}' already exists. Skipping creation.")

        contacts_table_name = os.getenv("DYNAMODB_TABLE_CONTACTS", "TazasContacts")
        if contacts_table_name not in existing_tables:
            print(f"Creating table '{contacts_table_name}'...")
            dynamodb.create_table(
                TableName=contacts_table_name,
                KeySchema=[
                    {"AttributeName": "phone_number", "KeyType": "HASH"}
                ],
                AttributeDefinitions=[
                    {"AttributeName": "phone_number", "AttributeType": "S"}
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            print(f"Table '{contacts_table_name}' creation requested...")
            dynamodb.get_waiter('table_exists').wait(TableName=contacts_table_name)
            print(f"Table '{contacts_table_name}' is now active.")
        else:
            print(f"Table '{contacts_table_name}' already exists.")

    except Exception as e:
        print(f"Error creating table: {e}")

if __name__ == "__main__":
    create_memory_table()
