from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.infrastructure.input.whatsapp_controller import router as whatsapp_router
from src.infrastructure.input.admin_controller import router as admin_router
from src.infrastructure.input.evaluation_controller import router as evaluation_router

app = FastAPI(
    title="Chatbot Tazas Personalizadas",
    description="API para el asistente virtual amigable de Tazas Personalizadas basado en LangGraph y Arquitectura Limpia.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permitir frontend dashboard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(whatsapp_router)
app.include_router(admin_router)
app.include_router(evaluation_router)

@app.get("/")
def root():
    return {"message": "API de Chatbot de Tazas Operativa. Anda al endpoint /docs para probar el bot."}
