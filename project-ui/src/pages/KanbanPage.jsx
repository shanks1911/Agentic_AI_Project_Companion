import React from "react";
import KanbanBoard from "../components/KanbanBoard";
import { useChat } from "../context/ChatContext";

export default function KanbanPage() {
  const { kanbanPlan } = useChat();

  return (
    <div className="page-container p-4">
      <h2 className="text-xl font-semibold mb-4">Kanban Plan</h2>
      {kanbanPlan ? <KanbanBoard plan={kanbanPlan} /> : <p>No Kanban plan generated yet. Chat on Home page first.</p>}
    </div>
  );
}
