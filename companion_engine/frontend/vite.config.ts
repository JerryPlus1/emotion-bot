import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite 开发服务器代理后端接口，避免浏览器跨端口 fetch 失败。
export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
      },
      "/health": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
      },
    },
  },
});
