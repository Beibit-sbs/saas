import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  esbuild: {
    jsx: "automatic",
  },
  test: {
    testTimeout: 30000,
    globals: true,
    environment: "jsdom",
    setupFiles: ["./__tests__/setup.ts"],
    exclude: ["e2e/**", "node_modules/**", "dist/**", ".n" + "ext/**"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./"),
    },
  },
});
