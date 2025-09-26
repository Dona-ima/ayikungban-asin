# app/routes/routes_chatbot.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.chatbot_api import get_response  # ta fonction du fichier converti

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chatbot/")
async def chatbot_endpoint(request: ChatRequest):
    try:
        response = get_response(request.message)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}
