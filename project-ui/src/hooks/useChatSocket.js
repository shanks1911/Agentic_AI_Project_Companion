// /root/project-ui/src/hooks/useChatSocket.js

import { useState, useEffect, useRef } from "react";

export default function useChatSocket() {
  const [messages, setMessages] = useState([]);
  const socketRef = useRef(null);

  useEffect(() => {
    socketRef.current = new WebSocket("ws://localhost:8000/ws/chat");

    socketRef.current.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      setMessages((prev) => [...prev, msg]);
    };

    return () => socketRef.current.close();
  }, []);

  const sendMessage = (text) => {
    const msg = { sender: "user", text };
    setMessages((prev) => [...prev, msg]);
    socketRef.current.send(text);
  };

  return { messages, sendMessage };
}
