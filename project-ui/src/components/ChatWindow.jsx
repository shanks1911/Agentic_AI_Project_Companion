// /src/components/ChatWindow.jsx
import React, { useRef, useState, useEffect } from "react";

const ChatWindow = ({ messages, sendMessage }) => {
  const [userInput, setUserInput] = useState("");
  const chatEndRef = useRef(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!userInput.trim()) return;
    sendMessage(userInput);
    setUserInput("");
  };

  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: "var(--chat-bg)" }}>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg max-w-[80%] wrap-break-word`}
            style={{
              alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
              backgroundColor: msg.sender === "user" ? "var(--user-msg-bg)" : "var(--ai-msg-bg)",
              color: "var(--text-color)",
            }}
          >
            <div>{msg.text}</div>

            {/* Render tasks if any */}
            {msg.type === "tasks" && msg.data?.tasks && (
              <ul className="mt-2 ml-4 list-disc">
                {msg.data.tasks.map((task) => (
                  <li key={task.id}>
                    <strong>{task.title}</strong>: {task.description}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      <div className="p-2 border-t" style={{ borderColor: "var(--border-color)" }}>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Type your message..."
            className="flex-1 p-2 rounded-lg border focus:outline-none"
            style={{
              backgroundColor: "var(--input-bg)",
              borderColor: "var(--input-border)",
              color: "var(--text-color)",
            }}
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
          />
          <button
            onClick={handleSend}
            className="px-4 py-2 rounded-lg font-semibold"
            style={{
              backgroundColor: "var(--button-bg)",
              color: "var(--text-color)",
            }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;
