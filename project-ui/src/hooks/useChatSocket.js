import { useEffect, useRef, useState } from "react";

const useChatSocket = (url = "ws://localhost:8000/ws/chat") => {
  const [messages, setMessages] = useState([]);
  const [tasks, setTasks] = useState(null);
  const [kanbanPlan, setKanbanPlan] = useState(null);
  const [ganttPlan, setGanttPlan] = useState(null);
  const ws = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket(url);

    ws.current.onopen = () => console.log("✅ WebSocket connected");

    ws.current.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log("WS MESSAGE:", msg);

        if (msg.type === "tasks") {
          setTasks({ tasks: msg.data.tasks || [] });
          setMessages(prev => [...prev, {
            sender: "ai",
            text: msg.text || "Here are initial tasks:",
            type: "tasks",
            data: msg.data
          }]);
          return;
        }

        if (msg.type === "kanban") {
          setKanbanPlan(msg.data);
          setMessages(prev => [...prev, { sender: "ai", text: "🗂️ Kanban plan ready!", type: "kanban", data: msg.data }]);
          return;
        }

        if (msg.type === "gantt") {
          setGanttPlan(msg.data);
          setMessages(prev => [...prev, { sender: "ai", text: "📅 Gantt chart ready!", type: "gantt", data: msg.data }]);
          return;
        }

        setMessages(prev => [...prev, msg]);
      } catch (err) {
        console.error("❌ WS parse error:", err);
      }
    };

    ws.current.onclose = () => console.log("🔒 WebSocket closed");
    ws.current.onerror = (err) => console.error("⚠️ WS error:", err);

    return () => ws.current && ws.current.close();
  }, [url]);

  const sendMessage = (text) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(text);
      setMessages(prev => [...prev, { sender: "user", text }]);
    } else {
      console.error("❌ Cannot send: WebSocket not connected");
    }
  };

  return { messages, sendMessage, tasks, kanbanPlan, ganttPlan };
};

export default useChatSocket;
