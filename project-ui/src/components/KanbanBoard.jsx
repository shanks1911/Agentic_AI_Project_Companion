// /src/components/KanbanBoard.jsx
import React from "react";

const KanbanBoard = ({ plan, tasks }) => {
  const columns = plan?.columns || [
    {
      name: "To-Do",
      tasks: tasks?.tasks || [],
    },
  ];

  if (!columns[0].tasks.length) {
    return <p className="text-center text-gray-400">No tasks available.</p>;
  }

  return (
    <div className="flex gap-4 overflow-x-auto p-4 rounded-lg" style={{ backgroundColor: "var(--chat-bg)" }}>
      {columns.map((col, i) => (
        <div
          key={i}
          className="shrink-0 w-64 p-3 rounded-lg shadow"
          style={{ backgroundColor: "var(--ai-msg-bg)" }}
        >
          <h3 className="text-center font-semibold border-b pb-1 mb-2" style={{ borderColor: "var(--border-color)", color: "var(--text-color)" }}>
            {col.name}
          </h3>
          {col.tasks.map((task, tIdx) => (
            <div
              key={tIdx}
              className="p-2 mb-2 rounded"
              style={{ backgroundColor: "var(--user-msg-bg)", color: "var(--text-color)" }}
            >
              <strong>{task.title || task.task_name}</strong>
              <p className="text-sm">{task.description || ""}</p>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

export default KanbanBoard;
