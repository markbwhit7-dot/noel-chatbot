const API_BASE_URL = '/api';

export interface ChatRequest {
  message: string;
  user_id?: string;
  conversation_id?: string;
}

export interface SourceDocument {
  chapter: string;
  section: string;
  page?: number;
  content: string;
  score?: number;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  sources: SourceDocument[];
  tokens_used?: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceDocument[];
  timestamp: Date;
}

export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to send message');
  }

  return response.json();
}

export async function getConversationHistory(conversationId: string): Promise<Message[]> {
  const response = await fetch(`${API_BASE_URL}/chat/history/${conversationId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch conversation history');
  }

  const data = await response.json();
  return data.messages;
}
