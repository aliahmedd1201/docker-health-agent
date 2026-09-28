import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // In local dev, forward /api requests to the backend on port 3000
    proxy: {
      "/api": "http://localhost:3000",
    },
  },
});