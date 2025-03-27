from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_id: int
    message: str


class ChatResponse(BaseModel):
    response: str
