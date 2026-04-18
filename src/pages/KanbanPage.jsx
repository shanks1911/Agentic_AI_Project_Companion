import { useChat } from "../context/ChatContext";

export default function KanbanPage() {
  const { project } = useChat();

  if (!project) {
    return <div className="text-gray-500">No project yet.</div>;
  }

  const tasks = project.tasks || [];

  const todo = tasks.filter(t => t.status === "To-Do" || t.status === "Not Started");
  const inProgress = tasks.filter(t => t.status === "In Progress");
  const done = tasks.filter(t => t.status === "Completed");

  const renderColumn = (title, items, color) => (
    <div className="flex-1">
      <h2 className="font-bold mb-2">{title}</h2>

      <div className="space-y-2">
        {items.map(task => (
          <div key={task.id} className={`p-3 rounded text-white ${color}`}>
            <div className="font-semibold">{task.title}</div>
            <div className="text-xs">{task.description}</div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">🧱 Kanban Board</h1>

      <div className="flex gap-4">
        {renderColumn("To-Do", todo, "bg-gray-500")}
        {renderColumn("In Progress", inProgress, "bg-yellow-500")}
        {renderColumn("Completed", done, "bg-green-600")}
      </div>
    </div>
  );
}