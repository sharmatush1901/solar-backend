from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.rag_service import ask_rag_stream

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    session_id: str


@router.post("/stream")
def stream_chat(req: ChatRequest):
    return StreamingResponse(
        ask_rag_stream(req.query, req.session_id),
        media_type="text/plain"
    )