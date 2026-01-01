from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4

from app.models.chat import ChatRequest, ChatResponse, SourceDocument
from app.core.config import Settings, get_settings
from app.services.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["chat"])

# Optional Supabase import
_supabase_available = False
try:
    from app.services.supabase_service import SupabaseService
    _supabase_available = True
except ImportError:
    pass


def get_rag_service(settings: Settings = Depends(get_settings)) -> RAGService:
    """Dependency to get RAG service instance."""
    return RAGService(settings)


def get_supabase_service(settings: Settings = Depends(get_settings)):
    """Dependency to get Supabase service instance (optional)."""
    if _supabase_available and settings.supabase_url and settings.supabase_key:
        return SupabaseService(settings)
    return None


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
    supabase_service=Depends(get_supabase_service),
) -> ChatResponse:
    """
    Process a chat message and return a response using RAG.

    - Retrieves relevant documents from Qdrant
    - Generates response using Claude with context
    - Stores conversation in Supabase (if configured)
    """
    conversation_id = request.conversation_id or str(uuid4())

    try:
        # Get conversation history if exists (only if Supabase configured)
        history = []
        if supabase_service and request.conversation_id and request.user_id:
            history = await supabase_service.get_conversation_history(
                request.conversation_id
            )

        # Generate response using RAG
        response, sources = await rag_service.generate_response(
            query=request.message,
            conversation_history=history,
        )

        # Store the conversation (only if Supabase configured)
        if supabase_service and request.user_id:
            await supabase_service.store_message(
                conversation_id=conversation_id,
                user_id=request.user_id,
                user_message=request.message,
                assistant_message=response,
            )

        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            sources=[
                SourceDocument(
                    chapter=s.get("chapter", "Unknown"),
                    section=s.get("section", ""),
                    page=s.get("page"),
                    content=s.get("content", ""),
                    score=s.get("score"),
                )
                for s in sources
            ],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{conversation_id}")
async def get_history(
    conversation_id: str,
    supabase_service=Depends(get_supabase_service),
):
    """Get conversation history by ID."""
    if not supabase_service:
        raise HTTPException(
            status_code=503,
            detail="Conversation history not available (Supabase not configured)"
        )
    history = await supabase_service.get_conversation_history(conversation_id)
    return {"conversation_id": conversation_id, "messages": history}
