# Asistente de Soporte con Grounding y Control de Alucinación

Este proyecto es la implementación de la **Opción 2 del Proyecto Final del curso "Fundamentos de Arquitectura LLM"**. Es un sistema de agente conversacional construido con LangGraph, FastAPI y DynamoDB, diseñado para una tienda virtual de tazas personalizadas ("Khronos").

El sistema demuestra la implementación práctica de técnicas anti-alucinación, Grounding (RAG), y Guardarraíles.

## 🚀 Requisitos Funcionales Cumplidos

1. **Base de Conocimiento Propia:** Conectado a Amazon DynamoDB (`TazasFAQ` y `TazasProducts`) como fuente externa (no hardcodeado).
2. **Modo Con y Sin Grounding:** Endpoint de evaluación (`/api/evaluate`) que permite alternar la inyección de contexto.
3. **Heurística Anti-Alucinación:** Nodo validador (`output_guardrail_node`) que cruza la respuesta generada por el LLM contra el contexto recuperado, marcando posibles invenciones.
4. **Manejo de Preguntas Fuera de Dominio:** Prompts ajustados para que el asistente admita explícitamente ignorancia si no encuentra información en la base de datos.

## 📁 Estructura del Proyecto

- `main.py`: Punto de entrada de FastAPI.
- `src/application/services/chatbot_orchestrator.py`: Grafo de LangGraph.
- `src/application/services/chatbot_nodes.py`: Nodos del grafo (Clasificador de intención, Generador, Heurística de Alucinación).
- `src/application/tools/`: Herramientas RAG (`rag_tools.py`) e Inventario (`inventory_tools.py`) que leen directamente desde DynamoDB.
- `src/infrastructure/input/evaluation_controller.py`: Endpoint diseñado específicamente para demostrar el proyecto (con/sin grounding).

## ⚙️ Cómo Ejecutarlo Localmente

Puedes correr este proyecto directamente con Docker:

```bash
docker-compose up --build
```

O si prefieres ejecutarlo nativamente con Python:

```bash
pip install -r requirements.txt
fastapi dev main.py
```

_Nota: Asegúrate de tener tus credenciales de AWS en el archivo `.env` en la raíz del proyecto._

## 🏗️ Arquitectura y Stack Tecnológico

Este proyecto implementa una arquitectura modular de agentes basada en flujos y grafos de estado. Se prioriza la separación de responsabilidades y el control estricto sobre las respuestas generadas mediante guardarraíles (Guardrails).

### Stack Tecnológico
- **Framework de Backend:** FastAPI (Python). Seleccionado por su alto rendimiento y generación automática de documentación interactiva (Swagger UI).
- **Orquestación de Agentes:** LangGraph. Utilizado para definir un flujo de control cíclico (ReAct), enrutamiento condicional y validación de salidas antes de llegar al usuario final.
- **Modelo de Lenguaje (LLM):** Azure OpenAI / Modelos locales vía Ollama.
- **Base de Datos y Persistencia:** Amazon DynamoDB (vía `boto3`). 
  - Actúa como la **Base de Conocimiento externa** para el sistema RAG (Tablas `TazasFAQ` e inventario).
  - Actúa como **Memoria a Corto/Largo Plazo** usando LangGraph Checkpointers para mantener el contexto de la conversación (`TazasChatHistory`).

### Flujo de la Arquitectura
1. **Entrada y Clasificación:** El input del usuario pasa por un nodo inicial (`intent_classifier_node`) que detecta intenciones maliciosas, inyecciones de prompt o evasiones, aplicando un *Input Guardrail*.
2. **Generación o Recuperación (Grounding):** Si la consulta requiere datos fácticos, el LLM decide invocar herramientas (Tool Nodes) que consultan la base de datos externa (DynamoDB).
3. **Validación de Salida (Heurística Anti-Alucinación):** Antes de retornar la respuesta, el sistema intercepta el mensaje en un `output_guardrail_node`. Aquí se cruza el contexto recuperado vs. la generación del LLM. Si se detecta información inventada o no respaldada, se adhiere una alerta al sistema y se reporta la desviación.

## ⚠️ Límites Conocidos del Sistema

De acuerdo con las mejores prácticas de la arquitectura LLM, este sistema presenta ciertas limitaciones documentadas:

1. **Latencia por Heurística (LLM-as-a-Judge):** La implementación de un nodo validador de salida requiere una segunda llamada secuencial al LLM para evaluar la respuesta generada. Esto garantiza precisión y fiabilidad, pero incrementa el tiempo de respuesta (latencia) de cara al usuario.
2. **Escalabilidad del "Recuperador" (RAG):** El sistema actual realiza un escaneo de tablas en DynamoDB. Si bien es ultraeficiente para el inventario actual (decenas de FAQs y productos), no escala para millones de documentos. A futuro, debería transicionar hacia una Base de Datos Vectorial (como Pinecone o pgvector) para permitir búsqueda semántica y recuperación por embeddings (`top_k`).
3. **Falsos Positivos en la Heurística:** Al usar un LLM como juez para la heurística anti-alucinación, pueden ocurrir casos marginales donde el modelo principal infiere una verdad basada en el sentido común de la conversación, pero el juez estricto lo marca como alucinación al no encontrar la palabra exacta en el contexto. 
4. **Dependencia Fuerte de la Calidad de los Datos:** El Grounding es tan bueno como los datos subyacentes. Si la base de datos no está actualizada (ej. stock agotado no reportado en DynamoDB), el sistema responderá con confianza datos desactualizados, lo cual el modelo no puede distinguir de una "verdad".
