from langchain_openai import AzureChatOpenAI
from src.providers.config import get_settings

class AzureOpenAIAdapter:
    def __init__(self):
        self.settings = get_settings()
        self.llm = AzureChatOpenAI(
            openai_api_version=self.settings.azure_openai_api_version,
            azure_endpoint=self.settings.azure_openai_endpoint,
            azure_deployment=self.settings.azure_openai_deployment_name,
            openai_api_key=self.settings.azure_openai_api_key,
            temperature=0.7 # Amigable y creativo
        )

    def get_llm(self) -> AzureChatOpenAI:
        return self.llm
