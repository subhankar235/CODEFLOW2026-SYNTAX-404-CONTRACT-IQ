from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.chat_pipeline import answer_question

router = APIRouter()

class ChatRequest(BaseModel):
    contract_id: str
    question: str


@router.post("/chat")
async def chat(req: ChatRequest):
    response = answer_question(
        contract_id=req.contract_id,
        question=req.question
    )

    return {
        "answer": response
    }