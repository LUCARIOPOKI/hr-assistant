import { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { ChatMessage } from './ChatMessage';
import { api } from '../services/api';

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

interface ChatInterfaceProps {
  isVisible: boolean;
}

export function ChatInterface({ isVisible }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      content: input.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const { query_id } = await api.query({
        query: userMessage.content,
        session_id: sessionId,
        user_id: 'default_user',
        top_k: 5,
      });

      let attempts = 0;
      const maxAttempts = 60;
      const pollInterval = 1000;

      const pollStatus = async () => {
        try {
          const status = await api.getStatus(query_id);

          if (status.status === 'completed' && status.answer) {
            const assistantMessage: Message = {
              id: `assistant_${Date.now()}`,
              content: status.answer,
              isUser: false,
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, assistantMessage]);
            setIsLoading(false);
            await api.clearStatus(query_id);
            return;
          }

          if (status.status === 'error') {
            throw new Error(status.error || 'An error occurred processing your query');
          }

          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(pollStatus, pollInterval);
          } else {
            throw new Error('Request timeout');
          }
        } catch (error) {
          console.error('Polling error:', error);
          throw error;
        }
      };

      await pollStatus();
    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        isUser: false,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      setIsLoading(false);
    }
  };

  return (
    <div
      className={`transition-all duration-700 ease-in-out ${
        isVisible
          ? 'w-full opacity-100'
          : 'w-0 opacity-0 overflow-hidden'
      }`}
    >
      <div className="flex flex-col h-screen bg-gradient-to-b from-[#3F4F44] to-[#2C3930]">
        <div className="bg-[#3F4F44] shadow-md border-b border-[#2C3930] px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-[#A27B5C]">
              <img
                src="https://images.pexels.com/photos/1239291/pexels-photo-1239291.jpeg?auto=compress&cs=tinysrgb&w=600"
                alt="Poki"
                className="w-full h-full object-cover"
              />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-[#A27B5C]">Poki</h2>
              <p className="text-sm text-[#DCD7C9]">Always here to help</p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center animate-fadeIn">
                <p className="text-lg text-[#DCD7C9] mb-4">Start a conversation!</p>
                <p className="text-sm text-[#A27B5C]">Ask me anything about HR policies and procedures</p>
              </div>
            </div>
          )}
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              content={message.content}
              isUser={message.isUser}
            />
          ))}
          {isLoading && <ChatMessage content="" isUser={false} isTyping />}
          <div ref={messagesEndRef} />
        </div>

        <div className="bg-[#3F4F44] border-t border-[#2C3930] px-6 py-4">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything about HR..."
              disabled={isLoading}
              className="flex-1 px-4 py-3 border-2 border-[#2C3930] rounded-full focus:outline-none focus:border-[#A27B5C] transition-colors text-[#DCD7C9] placeholder-[#A27B5C] disabled:bg-[#2C3930] bg-[#2C3930]"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-6 py-3 bg-[#A27B5C] text-white rounded-full hover:bg-[#8B6749] transition-all duration-300 disabled:bg-[#2C3930] disabled:cursor-not-allowed flex items-center gap-2 font-semibold shadow-lg hover:shadow-xl"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
