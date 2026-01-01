from datetime import datetime
from supabase import create_client, Client

from app.core.config import Settings


class SupabaseService:
    """Service for storing and retrieving conversation history from Supabase."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key,
        )
        self.table_name = "conversations"

    async def store_message(
        self,
        conversation_id: str,
        user_id: str,
        user_message: str,
        assistant_message: str,
    ) -> dict:
        """
        Store a conversation exchange in Supabase.

        Args:
            conversation_id: Unique conversation identifier
            user_id: User identifier
            user_message: The user's message
            assistant_message: The assistant's response

        Returns:
            The stored record
        """
        timestamp = datetime.utcnow().isoformat()

        # Store user message
        user_record = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": "user",
            "content": user_message,
            "created_at": timestamp,
        }

        # Store assistant message
        assistant_record = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": "assistant",
            "content": assistant_message,
            "created_at": timestamp,
        }

        # Insert both messages
        self.client.table(self.table_name).insert([user_record, assistant_record]).execute()

        return {"conversation_id": conversation_id, "stored": True}

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 20,
    ) -> list[dict]:
        """
        Retrieve conversation history from Supabase.

        Args:
            conversation_id: Unique conversation identifier
            limit: Maximum number of messages to retrieve

        Returns:
            List of messages in chronological order
        """
        response = (
            self.client.table(self.table_name)
            .select("role, content, created_at")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )

        return response.data if response.data else []

    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get a list of conversations for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of conversations to retrieve

        Returns:
            List of conversation summaries
        """
        # Get distinct conversation IDs for the user
        response = (
            self.client.table(self.table_name)
            .select("conversation_id, created_at, content")
            .eq("user_id", user_id)
            .eq("role", "user")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        # Group by conversation and get first message as preview
        conversations = {}
        for record in response.data or []:
            conv_id = record["conversation_id"]
            if conv_id not in conversations:
                conversations[conv_id] = {
                    "conversation_id": conv_id,
                    "preview": record["content"][:100],
                    "created_at": record["created_at"],
                }

        return list(conversations.values())

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            True if deleted successfully
        """
        self.client.table(self.table_name).delete().eq(
            "conversation_id", conversation_id
        ).execute()
        return True
