// /src/components/ThemeToggle.jsx
import React, { useState, useEffect } from "react";
import "../theme.css";

export default function ThemeToggle() {
  const [theme, setTheme] = useState("dark"); // 🌙 default dark mode

  useEffect(() => {
    if (theme === "light") {
      document.body.classList.add("light-mode");
    } else {
      document.body.classList.remove("light-mode");
    }
  }, [theme]);

  return (
    <button
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="theme-toggle-btn"
    >
      {theme === "dark" ? "Light Mode" : "Dark Mode"}
    </button>
  );
}
