import { MessageSquare } from 'lucide-react';

interface HeroSectionProps {
  isMinimized: boolean;
}

export function HeroSection({ isMinimized }: HeroSectionProps) {
  return (
    <div
      className={`transition-all duration-700 ease-in-out ${
        isMinimized
          ? 'w-0 opacity-0 overflow-hidden'
          : 'w-full opacity-100'
      }`}
    >
      <div className="flex flex-col items-center justify-center min-h-screen px-6 py-12">
        <div className="relative mb-8 animate-float">
          <div className="w-48 h-48 rounded-full overflow-hidden border-4 border-[#A27B5C] shadow-2xl">
            <img
              src="https://images.pexels.com/photos/1239291/pexels-photo-1239291.jpeg?auto=compress&cs=tinysrgb&w=600"
              alt="Poki"
              className="w-full h-full object-cover"
            />
          </div>
          <div className="absolute -bottom-2 -right-2 w-16 h-16 bg-[#A27B5C] rounded-full flex items-center justify-center shadow-lg animate-pulse">
            <MessageSquare className="w-8 h-8 text-[#A72703]" />
          </div>
        </div>

        <h1 className="text-5xl font-bold text-[#A27B5C] mb-4 text-center animate-slideUp">
          Welcome to Poki
        </h1>
        <p className="text-xl text-gray-300 mb-8 text-center max-w-2xl animate-slideUp" style={{ animationDelay: '100ms' }}>
          Your intelligent companion for all HR-related questions. Get instant answers about company policies, benefits, and procedures.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-4xl animate-slideUp" style={{ animationDelay: '200ms' }}>
          <div className="bg-[#3F4F44] rounded-xl p-6 shadow-md hover:shadow-xl transition-shadow duration-300 border-l-4 border-[#A27B5C]">
            <h3 className="font-semibold text-[#A27B5C] mb-2">Quick Answers</h3>
            <p className="text-sm text-[#DCD7C9]">Get instant responses to your HR queries</p>
          </div>
          <div className="bg-[#3F4F44] rounded-xl p-6 shadow-md hover:shadow-xl transition-shadow duration-300 border-l-4 border-[#A27B5C]">
            <h3 className="font-semibold text-[#A27B5C] mb-2">Policy Information</h3>
            <p className="text-sm text-[#DCD7C9]">Access comprehensive company policies</p>
          </div>
          <div className="bg-[#3F4F44] rounded-xl p-6 shadow-md hover:shadow-xl transition-shadow duration-300 border-l-4 border-[#A27B5C]">
            <h3 className="font-semibold text-[#A27B5C] mb-2">24/7 Availability</h3>
            <p className="text-sm text-[#DCD7C9]">Always here when you need assistance</p>
          </div>
        </div>
      </div>
    </div>
  );
}
