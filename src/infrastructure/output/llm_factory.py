from src.providers.config import get_settings
from src.infrastructure.output.azure_openai_adapter import AzureOpenAIAdapter
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel

class LLMFactory:
    def __init__(self):
        self.settings = get_settings()
        
    def get_llm(self) -> BaseChatModel:
        if self.settings.environment.lower() == "local":
            return ChatOllama(
                base_url=self.settings.ollama_base_url,
                model=self.settings.ollama_model,
                temperature=0.7
            )
        else:
            return AzureOpenAIAdapter().get_llm()
