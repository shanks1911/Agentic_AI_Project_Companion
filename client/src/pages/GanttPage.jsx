import { useChat } from "../context/ChatContext";

export default function GanttPage() {
  const { project } = useChat();

  if (!project) {
    return <div className="text-gray-500">No project yet.</div>;
  }

  const tasks = project.tasks || [];

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">📊 Gantt Chart</h1>

      <div className="space-y-3">
        {tasks.map(task => (
          <div key={task.id}>
            <div className="text-sm font-medium">{task.title}</div>

            <div className="w-full bg-gray-200 h-3 rounded mt-1">
              <div className="bg-blue-500 h-3 rounded w-2/3" />
            </div>

            <div className="text-xs text-gray-400">
              {task.start_date} → {task.end_date}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}