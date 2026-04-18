import { useChat } from "../context/ChatContext";

export default function TasksPage() {
  const { project } = useChat();

  if (!project) {
    return <div className="text-gray-500">No project yet. Generate one from Chat.</div>;
  }

  const tasks = project.tasks || [];

  const completed = tasks.filter(t => t.status === "Completed").length;

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">📋 Tasks</h1>

      <div className="mb-4">
        <div className="text-sm text-gray-600">
          {completed} / {tasks.length} completed
        </div>
        <div className="w-full bg-gray-200 rounded h-2 mt-1">
          <div
            className="bg-green-500 h-2 rounded"
            style={{ width: `${(completed / tasks.length) * 100}%` }}
          />
        </div>
      </div>

      <div className="space-y-3">
        {tasks.map(task => (
          <div key={task.id} className="bg-white p-4 rounded shadow">
            <div className="font-semibold">
              #{task.id} — {task.title}
            </div>

            <div className="text-sm text-gray-600 mt-1">
              {task.description}
            </div>

            <div className="text-xs text-gray-400 mt-2">
              {task.start_date} → {task.end_date}
            </div>

            <div className="mt-2 text-sm">
              Status: <span className="font-medium">{task.status}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}