// /src/context/ChatContext.jsx
import React, { createContext, useContext } from "react";
import useChatSocket from "../hooks/useChatSocket";

// Create context
const ChatContext = createContext();

// Provider component
export const ChatProvider = ({ children }) => {
  // Shared WebSocket state from the custom hook
  const { messages, sendMessage, kanbanPlan, ganttPlan } = useChatSocket();

  return (
    <ChatContext.Provider
      value={{
        messages,
        sendMessage,
        kanbanPlan,
        ganttPlan,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

// Custom hook for using chat context
export const useChat = () => useContext(ChatContext);
