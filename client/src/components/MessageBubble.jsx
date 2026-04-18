export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  let parsed = null;

  try {
    parsed = typeof message.content === "string"
      ? JSON.parse(message.content)
      : message.content;
  } catch {
    parsed = null;
  }

  const isProjectPlan =
    parsed &&
    typeof parsed === "object" &&
    parsed.title &&
    Array.isArray(parsed.tasks);

  if (isProjectPlan) {
    return (
      <div className="bg-white p-4 rounded-lg shadow max-w-2xl">
        <h2 className="text-lg font-bold text-blue-600 mb-1">
          📌 {parsed.title}
        </h2>

        <p className="text-gray-600 mb-3">{parsed.description}</p>

        <div className="space-y-3">
          {parsed.tasks.map((task) => (
            <div
              key={task.id}
              className="bg-gray-50 p-3 rounded border"
            >
              <div className="font-semibold text-sm">
                #{task.id} — {task.title}
              </div>

              <div className="text-sm text-gray-600 mt-1">
                {task.description}
              </div>

              <div className="text-xs text-gray-400 mt-1">
                {task.start_date} → {task.end_date}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // fallback
  return (
    <div
      className={`p-3 rounded max-w-xl whitespace-pre-wrap ${
        isUser
          ? "bg-blue-500 text-white ml-auto"
          : "bg-white shadow"
      }`}
    >
      {message.content}
    </div>
  );
}