import { createContext, useContext, useEffect, useRef, useState } from "react";

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const socketRef = useRef(null);

  const [messages, setMessages] = useState([]);
  const [toolLogs, setToolLogs] = useState([]);
  const [status, setStatus] = useState("");
  const [project, setProject] = useState(null);

  useEffect(() => {
    socketRef.current = new WebSocket("ws://localhost:8000/ws/chat");

    socketRef.current.onopen = () => {
      console.log("✅ Connected to WebSocket");
    };

    socketRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "final_response":
            setStatus("");

            try {
                let content = data.data;

                if (content.startsWith("```")) {
                content = content.replace(/```json|```/g, "").trim();
                }

                const parsed = JSON.parse(content);

                if (parsed.title && parsed.tasks) {
                setProject(parsed); // 🔥 STORE PROJECT
                }

                setMessages((prev) => [
                ...prev,
                { role: "assistant", content: content }
                ]);
            } catch {
                setMessages((prev) => [
                ...prev,
                { role: "assistant", content: data.data }
                ]);
            }
            break;

        case "tool_start":
          setToolLogs((prev) => [...prev.slice(-4), `🔧 ${data.data}`]);
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

//   useEffect(() => {
//     localStorage.setItem("chat_messages", JSON.stringify(messages));
//         const [messages, setMessages] = useState(() => {
//         const saved = localStorage.getItem("chat_messages");
//         return saved ? JSON.parse(saved) : [];
//         });
//     }, [messages]);


  const sendMessage = (message) => {
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    socketRef.current.send(JSON.stringify({ message }));
  };

  return (
    <ChatContext.Provider value={{ messages, sendMessage, toolLogs, status, project }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => useContext(ChatContext);