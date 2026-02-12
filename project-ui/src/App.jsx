// /src/App.jsx
import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import HomePage from "./pages/HomePage";
import KanbanPage from "./pages/KanbanPage";
import GanttPage from "./pages/GanttPage";
import ThemeToggle from "./components/ThemeToggle";
import { ChatProvider } from "./context/ChatContext";
import "./App.css";

export default function App() {
  return (
    <ChatProvider>
      <Router>
        <div className="app-container">
          <nav className="navbar">
            <h1>Project Planner AI</h1>
            <div>
              <Link to="/">Home</Link>
              <Link to="/kanban">Kanban</Link>
              <Link to="/gantt">Gantt</Link>
              <ThemeToggle />
            </div>
          </nav>

          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/kanban" element={<KanbanPage />} />
            <Route path="/gantt" element={<GanttPage />} />
          </Routes>
        </div>
      </Router>
    </ChatProvider>
  );
}
