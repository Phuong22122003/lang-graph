from fastapi import APIRouter, Depends
from app.schemas import PromptRequest, PromptResponse
import app.service.agent_service as agent_service
router = APIRouter()

@router.post("/")
def ask_agent(request: PromptRequest) -> PromptResponse:
    return agent_service.ask(request)

@router.get("/models")
def get_models():
    return [
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite',
        'gemini-2.5-flash',
        'gemini-2.5-flash-lite',
        'gemini-2.5-pro',
    ]

@router.post("/models/{model_name}")
def change_model(model_name:str):
    agent_service.change_model(f'google_genai:{model_name}')

@router.post("/memory/clear")
def clear_memory():
    agent_service.clear_memory()
    return {"status": "success"}