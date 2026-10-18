import { defineConfig } from "vite";

export default defineConfig({
  server: {
    port: 5180,
    proxy: {
      "/dashboard": "http://127.0.0.1:8010",
      "/queue": "http://127.0.0.1:8010",
      "/results": "http://127.0.0.1:8010",
      "/student-results": "http://127.0.0.1:8010",
      "/students": "http://127.0.0.1:8010",
      "/lecturer-decision": "http://127.0.0.1:8010",
    },
  },
});
