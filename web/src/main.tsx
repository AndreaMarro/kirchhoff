import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./app/App.tsx";
import "./design/tokens.css";
import "./app/app.css";

const root = document.getElementById("root");
if (!root) throw new Error("manca #root");
createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
