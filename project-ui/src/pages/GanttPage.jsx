import React from "react";
import GanttChart from "../components/GanttChart";
import { useChat } from "../context/ChatContext";

export default function GanttPage() {
  const { ganttPlan } = useChat();

  return (
    <div className="page-container p-4">
      <h2 className="text-xl font-semibold mb-4">Gantt Chart</h2>
      {ganttPlan ? <GanttChart plan={ganttPlan} /> : <p>No Gantt plan generated yet. Chat on Home page first.</p>}
    </div>
  );
}
