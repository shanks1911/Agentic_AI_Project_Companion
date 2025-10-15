// /src/App.jsx
import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";
import ThemeToggle from "./components/themeToggle"; // ✅ new import

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const socketRef = useRef(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    socketRef.current = new WebSocket("ws://localhost:8000/ws/chat");

    socketRef.current.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        setMessages((prev) => [...prev, msg]);
        setIsTyping(false);
      } catch {
        console.error("Failed to parse message");
      }
    };

    return () => socketRef.current.close();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    if (socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(input);
    }
    setInput("");
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Project Companion AI</h1>
        <ThemeToggle /> {/* ✅ Light/Dark mode button */}
      </div>

      <div className="chat-window">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`chat-message ${msg.sender === "user" ? "user" : "ai"}`}
          >
            <ReactMarkdown>{msg.text}</ReactMarkdown>
          </div>
        ))}

        {isTyping && (
          <div className="chat-message ai typing">
            <span className="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </span>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <form onSubmit={sendMessage} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}

export default App;
