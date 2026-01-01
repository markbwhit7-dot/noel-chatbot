import { useState, useRef, useEffect } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { sendMessage, Message } from '../services/api';
import './ChatWindow.css';

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (content: string) => {
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendMessage({
        message: content,
        conversation_id: conversationId ?? undefined,
      });

      setConversationId(response.conversation_id);

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.response,
        sources: response.sources,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(null);
    setError(null);
  };

  return (
    <div className="chat-window">
      <header className="chat-header">
        <div className="chat-header-content">
          <h1>Noel Whittaker</h1>
          <p>Financial Education Assistant</p>
        </div>
        {messages.length > 0 && (
          <button className="new-chat-button" onClick={handleNewChat}>
            New Chat
          </button>
        )}
      </header>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <div className="welcome-icon">💰</div>
            <h2>Welcome!</h2>
            <p>
              I'm here to help you learn about personal finance, investing,
              superannuation, and building wealth. Ask me anything!
            </p>
            <div className="welcome-suggestions">
              <button onClick={() => handleSend("What are the basics of investing?")}>
                What are the basics of investing?
              </button>
              <button onClick={() => handleSend("How does superannuation work?")}>
                How does superannuation work?
              </button>
              <button onClick={() => handleSend("Tips for paying off a mortgage faster")}>
                Tips for paying off a mortgage faster
              </button>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))
        )}

        {isLoading && (
          <div className="chat-message assistant">
            <div className="message-avatar">💰</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="chat-error">
            <p>Error: {error}</p>
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  );
}
