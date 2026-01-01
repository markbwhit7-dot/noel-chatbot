import { Message } from '../services/api';
import './ChatMessage.css';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`chat-message ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '💰'}
      </div>
      <div className="message-content">
        <div className="message-header">
          <span className="message-role">
            {isUser ? 'You' : 'Noel'}
          </span>
          <span className="message-time">
            {message.timestamp.toLocaleTimeString()}
          </span>
        </div>
        <div className="message-text">{message.content}</div>
        {message.sources && message.sources.length > 0 && (
          <div className="message-sources">
            <details>
              <summary>Sources ({message.sources.length})</summary>
              <ul>
                {message.sources.map((source, index) => (
                  <li key={index}>
                    <strong>{source.chapter}</strong>
                    {source.page && <span className="source-page"> (p. {source.page})</span>}
                    <span className="source-section">{source.section}</span>
                    <p>{source.content}</p>
                  </li>
                ))}
              </ul>
            </details>
          </div>
        )}
      </div>
    </div>
  );
}
