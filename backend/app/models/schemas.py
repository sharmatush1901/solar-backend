from pydantic import BaseModel

# Solar API schema
class SolarInput(BaseModel):
    area: float
    sunlight_hours: float


# Chat API schema (with memory)
class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"