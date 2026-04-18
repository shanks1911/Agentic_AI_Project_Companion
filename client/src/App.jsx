import { BrowserRouter, Routes, Route } from "react-router-dom";
import DashboardLayout from "./layout/DashboardLayout";

import ChatPage from "./pages/ChatPage";
import TasksPage from "./pages/TasksPage";
import KanbanPage from "./pages/KanbanPage";
import GanttPage from "./pages/GanttPage";

function App() {
  return (
    <BrowserRouter>
      <DashboardLayout>
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/tasks" element={<TasksPage />} />
          <Route path="/kanban" element={<KanbanPage />} />
          <Route path="/gantt" element={<GanttPage />} />
        </Routes>
      </DashboardLayout>
    </BrowserRouter>
  );
}

export default App;