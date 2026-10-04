import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Cargamos el .env explícitamente para que os.getenv lo lea
load_dotenv()
load_dotenv("../../.env")

class Settings(BaseSettings):
    environment: str = os.getenv("ENVIRONMENT", "prod")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    dynamodb_local_endpoint: str = os.getenv("DYNAMODB_LOCAL_ENDPOINT", "http://localhost:8000")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3-vl:8b")

    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    azure_openai_deployment_name: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
    
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_default_region: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    dynamodb_table_products: str = os.getenv("DYNAMODB_TABLE_PRODUCTS", "TazasProducts")
    dynamodb_table_faq: str = os.getenv("DYNAMODB_TABLE_FAQ", "TazasFAQ")
    dynamodb_table_memory: str = os.getenv("DYNAMODB_TABLE_MEMORY", "TazasChatHistory")
    dynamodb_table_contacts: str = os.getenv("DYNAMODB_TABLE_CONTACTS", "TazasContacts")

    whatsapp_token: str = os.getenv("WHATSAPP_TOKEN", "")
    whatsapp_verify_token: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    whatsapp_phone_number_id: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    inventory_api_url: str = os.getenv("INVENTORY_API_URL", "http://localhost:8001/api/v1")

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"), 
        env_file_encoding="utf-8"
    )

def get_settings() -> Settings:
    return Settings()
