import React, { useState } from "react";
import ChatWindow from "../components/ChatWindow";
import KanbanBoard from "../components/KanbanBoard";
import GanttChart from "../components/GanttChart";
import { useChat } from "../context/ChatContext";

export default function HomePage() {
  const { messages, sendMessage, tasks, kanbanPlan, ganttPlan } = useChat();
  const [tasksConfirmed, setTasksConfirmed] = useState(false);

  const handleConfirmTasks = () => {
    sendMessage("confirm");
    setTasksConfirmed(true);
  };

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: "var(--bg-color)", color: "var(--text-color)" }}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <div className="h-[80vh] rounded-lg shadow flex flex-col">
          <ChatWindow messages={messages} sendMessage={sendMessage} />
        </div>

        <div className="h-[80vh] overflow-y-auto flex flex-col gap-4">

          {/* Tasks Preview */}
          {tasks && !tasksConfirmed && (
            <div className="p-4 rounded-lg shadow space-y-2" style={{ backgroundColor: "var(--chat-bg)" }}>
              <h3 className="font-semibold text-lg">📝 Initial Tasks Preview</h3>
              <KanbanBoard tasks={tasks} />
              <button
                onClick={handleConfirmTasks}
                className="mt-2 px-4 py-2 rounded font-semibold"
                style={{ backgroundColor: "var(--button-bg)", color: "var(--text-color)" }}
              >
                ✅ Confirm Tasks
              </button>
            </div>
          )}

          {/* Final Plans */}
          {tasksConfirmed && kanbanPlan && (
            <div className="p-4 rounded-lg shadow space-y-2" style={{ backgroundColor: "var(--chat-bg)" }}>
              <h3 className="font-semibold text-lg">🗂️ Kanban Plan</h3>
              <KanbanBoard plan={kanbanPlan} />
            </div>
          )}
          {tasksConfirmed && ganttPlan && (
            <div className="p-4 rounded-lg shadow space-y-2" style={{ backgroundColor: "var(--chat-bg)" }}>
              <h3 className="font-semibold text-lg">📅 Gantt Chart</h3>
              <GanttChart plan={ganttPlan} />
            </div>
          )}

          {!tasks && !kanbanPlan && !ganttPlan && (
            <p className="text-center text-gray-400">Waiting for tasks from the backend...</p>
          )}
        </div>
      </div>
    </div>
  );
}
