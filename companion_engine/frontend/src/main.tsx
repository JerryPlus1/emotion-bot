import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

// React 入口，挂载整个 Demo 应用。
createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
