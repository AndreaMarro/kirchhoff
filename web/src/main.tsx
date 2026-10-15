import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./app/App.tsx";
import { StudentApp } from "./student/StudentApp.tsx";
import "./design/tokens.css";
import "./app/app.css";

const root = document.getElementById("root");
if (!root) throw new Error("manca #root");
createRoot(root).render(
  <StrictMode>
    {new URLSearchParams(location.search).get('view') === 'proof' ? <App /> : <StudentApp />}
  </StrictMode>,
);
