import { useState, useEffect } from 'react';
import { HeroSection } from './components/HeroSection';
import { ChatInterface } from './components/ChatInterface';

function App() {
  const [chatStarted, setChatStarted] = useState(false);
  const [showChat, setShowChat] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setChatStarted(true);
      setTimeout(() => setShowChat(true), 300);
    }, 3000);

    const handleClick = () => {
      if (!chatStarted) {
        clearTimeout(timer);
        setChatStarted(true);
        setTimeout(() => setShowChat(true), 300);
      }
    };

    window.addEventListener('click', handleClick);

    return () => {
      clearTimeout(timer);
      window.removeEventListener('click', handleClick);
    };
  }, [chatStarted]);

  return (
    <div className="flex w-full min-h-screen bg-gradient-to-br from-[#2C3930] via-[#3F4F44] to-[#2C3930]">
      <HeroSection isMinimized={chatStarted} />
      <ChatInterface isVisible={showChat} />
    </div>
  );
}

export default App;
