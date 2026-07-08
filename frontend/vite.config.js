import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// El proxy evita CORS en desarrollo: el frontend usa rutas relativas
// (/api, /media) y Vite las reenvía al backend Flask.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": "http://localhost:5000",
      "/media": "http://localhost:5000",
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./tests/setup.js",
    globals: true,
  },
});
