from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """A single chat message."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Request payload for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=2000)
    user_id: str | None = None
    conversation_id: str | None = None


class SourceDocument(BaseModel):
    """A source document used to generate the response."""

    chapter: str
    section: str = ""
    page: int | None = None
    content: str
    score: float | None = None


class ChatResponse(BaseModel):
    """Response payload from chat endpoint."""

    response: str
    conversation_id: str
    sources: list[SourceDocument] = []
    tokens_used: int | None = None


class ConversationHistory(BaseModel):
    """Stored conversation history."""

    conversation_id: str
    user_id: str | None = None
    messages: list[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
