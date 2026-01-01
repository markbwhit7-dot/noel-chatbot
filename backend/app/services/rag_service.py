from llama_index.core import VectorStoreIndex, Settings as LlamaSettings
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from qdrant_client import QdrantClient, AsyncQdrantClient

from app.core.config import Settings
from app.models.chat import ChatMessage


class RAGService:
    """Service for RAG-based question answering using LlamaIndex."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._setup_llama_index()

    def _setup_llama_index(self):
        """Initialize LlamaIndex components."""
        # Set up LLM (Groq - free and fast)
        self.llm = Groq(
            api_key=self.settings.groq_api_key,
            model=self.settings.groq_model,
        )

        # Set up embeddings (local model, matches Qdrant ingestion)
        self.embed_model = HuggingFaceEmbedding(
            model_name=self.settings.embedding_model,
        )

        # Configure LlamaIndex settings
        LlamaSettings.llm = self.llm
        LlamaSettings.embed_model = self.embed_model
        LlamaSettings.chunk_size = self.settings.chunk_size
        LlamaSettings.chunk_overlap = self.settings.chunk_overlap

        # Set up Qdrant clients (sync and async)
        self.qdrant_client = QdrantClient(
            url=self.settings.qdrant_url,
            api_key=self.settings.qdrant_api_key,
        )
        self.async_qdrant_client = AsyncQdrantClient(
            url=self.settings.qdrant_url,
            api_key=self.settings.qdrant_api_key,
        )

        # Set up vector store with both clients
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            aclient=self.async_qdrant_client,
            collection_name=self.settings.qdrant_collection_name,
        )

        # Create index from existing vector store
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
        )

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the chatbot."""
        return """You are a helpful financial education assistant based on the teachings
and wisdom of Noel Whittaker, a renowned Australian financial advisor and author.

Your role is to:
- Provide clear, practical financial education and guidance
- Explain complex financial concepts in simple terms
- Help users understand investment, superannuation, and wealth-building principles
- Always emphasize the importance of seeking professional advice for specific situations

Important guidelines:
- Be encouraging but realistic about financial goals
- Never provide specific investment recommendations or financial advice for individual situations
- Always remind users to consult with a licensed financial advisor for personalized advice
- Base your responses on the provided context from Noel Whittaker's materials
- If you don't have information on a topic, say so honestly

Remember: Education empowers people to make better financial decisions."""

    async def generate_response(
        self,
        query: str,
        conversation_history: list[dict] | None = None,
    ) -> tuple[str, list[dict]]:
        """
        Generate a response using RAG.

        Args:
            query: The user's question
            conversation_history: Previous messages in the conversation

        Returns:
            Tuple of (response text, list of source documents)
        """
        # Build chat history for context
        chat_history = []
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages
                chat_history.append(
                    ChatMessage(role=msg["role"], content=msg["content"])
                )

        # Create query engine with top_k
        query_engine = self.index.as_query_engine(
            similarity_top_k=self.settings.top_k,
            system_prompt=self._build_system_prompt(),
        )

        # Create chat engine for conversation context
        chat_engine = CondenseQuestionChatEngine.from_defaults(
            query_engine=query_engine,
            llm=self.llm,
        )

        # Generate response
        response = await chat_engine.achat(query)

        # Extract source documents
        sources = []
        if response.source_nodes:
            for node in response.source_nodes:
                sources.append({
                    "chapter": node.metadata.get("chapter_title", "Unknown"),
                    "section": node.metadata.get("section", ""),
                    "page": node.metadata.get("page_start", ""),
                    "content": node.text[:500],  # Truncate for response
                    "score": node.score,
                })

        return str(response), sources
