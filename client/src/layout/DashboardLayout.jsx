import { Link } from "react-router-dom";

export default function DashboardLayout({ children }) {
  return (
    <div className="flex h-screen">

      {/* Sidebar */}
      <div className="w-64 bg-gray-900 text-white p-4">
        <h1 className="text-xl font-bold mb-6">🤖 Agentic AI</h1>

        <nav className="space-y-3">
          <Link to="/" className="block hover:text-blue-400">💬 Chat</Link>
          <Link to="/tasks" className="block hover:text-blue-400">📋 Tasks</Link>
          <Link to="/kanban" className="block hover:text-blue-400">🧱 Kanban</Link>
          <Link to="/gantt" className="block hover:text-blue-400">📊 Gantt</Link>
        </nav>
      </div>

      {/* Main */}
      <div className="flex-1 p-6 bg-gray-100 overflow-auto">
        {children}
      </div>
    </div>
  );
}