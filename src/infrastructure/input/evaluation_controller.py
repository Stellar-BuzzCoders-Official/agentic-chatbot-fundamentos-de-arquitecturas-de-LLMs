from fastapi import APIRouter
from pydantic import BaseModel
from src.application.services.chatbot_orchestrator import ChatbotOrchestrator
import uuid

router = APIRouter(prefix="/api/evaluate", tags=["Evaluation"])

orchestrator = ChatbotOrchestrator()

class EvaluationRequest(BaseModel):
    message: str
    use_grounding: bool = True
    thread_id: str = None  # Opcional para mantener el historial de la charla

@router.post("")
async def evaluate_chat(request: EvaluationRequest):
    """
    Endpoint para probar respuestas con y sin grounding (RAG/Herramientas).
    Si use_grounding=True, pasa por todo el grafo de LangGraph.
    Si use_grounding=False, bypass al LLM directamente.
    """
    # Usar el thread_id enviado o generar uno nuevo si es None
    current_thread_id = request.thread_id if request.thread_id else str(uuid.uuid4())
    
    if request.use_grounding:
        response_text, _ = await orchestrator.ainvoke(request.message, thread_id=current_thread_id)
        return {
            "grounding_active": True, 
            "thread_id": current_thread_id,
            "response": response_text
        }
    else:
        # Bypassear herramientas y context
        response_text = await orchestrator.ainvoke_without_grounding(request.message)
        return {
            "grounding_active": False, 
            "thread_id": current_thread_id,
            "response": response_text
        }
