// /src/components/GanttChart.jsx
import React from "react";

const GanttChart = ({ plan, tasks }) => {
  const taskList = plan?.tasks || tasks?.tasks || [];

  if (!taskList.length) {
    return <p className="text-center text-gray-400">No Gantt data available.</p>;
  }

  const startDates = taskList.map((t) => new Date(t.start_date || t.start));
  const endDates = taskList.map((t) => new Date(t.end_date || t.end));
  const minDate = new Date(Math.min(...startDates));
  const maxDate = new Date(Math.max(...endDates));

  const calcLeft = (start) => ((new Date(start) - minDate) / (maxDate - minDate)) * 100;
  const calcWidth = (start, end) => ((new Date(end) - new Date(start)) / (maxDate - minDate)) * 100;

  return (
    <div className="p-4 rounded-lg shadow space-y-2" style={{ backgroundColor: "var(--chat-bg)" }}>
      {taskList.map((task, idx) => (
        <div key={idx}>
          <strong style={{ color: "var(--text-color)" }}>{task.task_name || task.title}</strong>
          <div className="relative h-6 rounded mt-1" style={{ backgroundColor: "var(--ai-msg-bg)" }}>
            {task.start_date && task.end_date && (
              <div
                className="absolute h-full rounded"
                style={{
                  left: `${calcLeft(task.start_date)}%`,
                  width: `${calcWidth(task.start_date, task.end_date)}%`,
                  backgroundColor: "var(--user-msg-bg)",
                }}
              ></div>
            )}
          </div>
          <small style={{ color: "var(--text-color)" }}>
            {task.start_date || task.start} → {task.end_date || task.end}
          </small>
        </div>
      ))}
    </div>
  );
};

export default GanttChart;
