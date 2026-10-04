from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage

from langgraph_checkpoint_aws import DynamoDBSaver
import boto3
from src.providers.config import get_settings

from src.infrastructure.output.llm_factory import LLMFactory
from src.application.tools.inventory_tools import check_inventory
from src.application.tools.rag_tools import get_faq_and_policies

from src.application.services.agent_state import AgentState
from src.application.services.chatbot_nodes import ChatbotNodes
from langchain_core.messages import SystemMessage


class ChatbotOrchestrator:
    def __init__(self):
        llm_factory = LLMFactory()
        self.llm = llm_factory.get_llm()
        self.tools = [check_inventory, get_faq_and_policies]
        self.tool_node = ToolNode(self.tools)
        self.assistant_runnable = self.llm.bind_tools(self.tools)

        # Inicializar los nodos refactorizados
        self.chatbot_nodes = ChatbotNodes(self.llm, self.assistant_runnable)

        # Construir el grafo
        builder = StateGraph(AgentState)

        builder.add_node("intent_classifier",
                         self.chatbot_nodes.intent_classifier_node)
        builder.add_node("assistant", self.chatbot_nodes.assistant_node)
        builder.add_node("tools", self.tool_node)
        builder.add_node("output_guardrail",
                         self.chatbot_nodes.output_guardrail_node)

        builder.add_edge(START, "intent_classifier")
        builder.add_conditional_edges(
            "intent_classifier", self.chatbot_nodes.route_input)

        builder.add_conditional_edges(
            "assistant", self.chatbot_nodes.route_assistant)
        builder.add_edge("tools", "assistant")

        builder.add_conditional_edges(
            "output_guardrail", self.chatbot_nodes.route_output)

        settings = get_settings()

        boto_session_args = {
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
            "region_name": settings.aws_default_region
        }

        # Inyectar endpoint local si el entorno es 'local'
        if settings.environment.lower() == "local":
            pass

        boto_session = boto3.Session(**boto_session_args)

        saver_kwargs = {
            "table_name": settings.dynamodb_table_memory,
            "session": boto_session
        }

        if settings.environment.lower() == "local":
            saver_kwargs["endpoint_url"] = settings.dynamodb_local_endpoint

        self.saver = DynamoDBSaver(**saver_kwargs)

        self.app = builder.compile(checkpointer=self.saver)

    def invoke(self, message: str, thread_id: str = "default_thread") -> tuple[str, bool]:
        inputs = {"messages": [HumanMessage(content=message)]}
        config = {"configurable": {"thread_id": thread_id}}

        response = self.app.invoke(inputs, config=config)
        return response["messages"][-1].content, response.get("request_handoff", False)

    async def ainvoke(self, message: str, thread_id: str = "default_thread") -> tuple[str, bool]:
        inputs = {"messages": [HumanMessage(content=message)]}
        config = {"configurable": {"thread_id": thread_id}}

        response = await self.app.ainvoke(inputs, config=config)

        final_text = response["messages"][-1].content

        return final_text, response.get("request_handoff", False)

    async def ainvoke_without_grounding(self, message: str) -> str:
        """Llama al LLM directamente sin RAG, herramientas ni historial, para demostrar alucinación."""

        # Usamos un prompt genérico (sin nuestras reglas estrictas) para que el modelo alucine e invente información
        GENERIC_PROMPT = "Eres el asistente virtual de la tienda de tazas personalizadas Khronos. Responde a las dudas de los clientes de forma segura y directa, dándoles la información de envíos y tiempos que te pidan."

        messages = [
            SystemMessage(content=GENERIC_PROMPT),
            HumanMessage(content=message)
        ]

        response = await self.llm.ainvoke(messages)
        return response.content
