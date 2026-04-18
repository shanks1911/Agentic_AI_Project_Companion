import { useEffect, useRef, useState } from "react";

export default function useSocket() {
  const socketRef = useRef(null);
  const [messages, setMessages] = useState([]);
  const [toolLogs, setToolLogs] = useState([]);
  const [status, setStatus] = useState("");

  useEffect(() => {
    socketRef.current = new WebSocket("ws://localhost:8000/ws/chat");

    socketRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "user_message":
          setMessages((prev) => [...prev, { role: "user", content: data.data }]);
          break;

        case "final_response":
          setMessages((prev) => [...prev, { role: "assistant", content: data.data }]);
          break;

        case "tool_start":
          setToolLogs((prev) => [...prev, `🔧 ${data.data}`]);
          break;

        case "status":
          setStatus(data.data);
          break;

        default:
          break;
      }
    };

    return () => socketRef.current.close();
  }, []);

  const sendMessage = (message) => {
    socketRef.current.send(JSON.stringify({ message }));
  };

  return { messages, sendMessage, toolLogs, status };
}