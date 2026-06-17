from pydantic import BaseModel
from typing import List, Optional, Literal


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class TriageRequest(BaseModel):
    conversation: List[Message]
    language: str = "en"


class TriageResponse(BaseModel):
    reply: str
    urgency: Optional[Literal["home_care", "visit_phc", "critical", "unclear"]] = None
    is_final: bool = False
    source: Optional[str] = None