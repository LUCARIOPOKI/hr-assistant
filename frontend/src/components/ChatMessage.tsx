import { User, Bot } from 'lucide-react';

interface ChatMessageProps {
  content: string;
  isUser: boolean;
  isTyping?: boolean;
}

export function ChatMessage({ content, isUser, isTyping }: ChatMessageProps) {
  return (
    <div
      className={`flex gap-3 mb-4 animate-fadeIn ${
        isUser ? 'justify-end' : 'justify-start'
      }`}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-[#A27B5C] flex items-center justify-center">
          <Bot className="w-5 h-5 text-white" />
        </div>
      )}
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-[#A27B5C] text-white'
            : 'bg-[#3F4F44] text-[#DCD7C9] border border-[#2C3930]'
        }`}
      >
        {isTyping ? (
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-[#A27B5C] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
            <span className="w-2 h-2 bg-[#A27B5C] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
            <span className="w-2 h-2 bg-[#A27B5C] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
          </div>
        ) : (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        )}
      </div>
      {isUser && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-[#A27B5C] flex items-center justify-center">
          <User className="w-5 h-5 text-white" />
        </div>
      )}
    </div>
  );
}
