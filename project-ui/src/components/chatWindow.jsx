// /root/project-ui/src/components/chatWindow.jsx

import React, { useState } from "react";
import useChatSocket from "../hooks/useChatSocket";

export default function ChatWindow() {
  const { messages, sendMessage } = useChatSocket();
  const [input, setInput] = useState("");

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage(input);
    setInput("");
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.sender}`}>
            <b>{m.sender === "user" ? "You" : "🤖 AI"}:</b> {m.text}
          </div>
        ))}
      </div>
      <form onSubmit={handleSend}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
