import { useState } from "react";
import { useChat } from "../context/ChatContext";
import MessageBubble from "../components/MessageBubble";

export default function ChatPage() {
  const { messages, sendMessage, toolLogs, status } = useChat();
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input) return;
    sendMessage(input);
    setInput("");
  };

  return (
    <div className="flex h-full">

      {/* Chat */}
      <div className="flex-1 flex flex-col">

        <div className="flex-1 overflow-auto space-y-3 mb-4">
          {messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} />
          ))}
        </div>

        {status === "thinking" && (
          <div className="text-gray-500 mb-2">🤖 Thinking...</div>
        )}

        <div className="flex gap-2">
          <input
            className="flex-1 border p-2 rounded"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button
            onClick={handleSend}
            className="bg-blue-500 text-white px-4 rounded"
          >
            Send
          </button>
        </div>
      </div>

      {/* Tool Panel */}
      <div className="w-64 ml-4 bg-white shadow p-3">
        <h2 className="font-bold mb-2">🔧 Activity</h2>
        {toolLogs.map((log, i) => (
          <div key={i} className="text-sm mb-1">{log}</div>
        ))}
      </div>

    </div>
  );
}