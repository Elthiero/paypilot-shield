import { defineConfig } from "@playwright/test";

const py = process.env.E2E_PYTHON ?? "python";  // CI uses the system python, locally point it at backend/venv/bin/python
const env = { APP_ENV: "development", PAYPAL_MODE: "fake", DATABASE_URL: "sqlite+pysqlite:///./e2e.db", JWT_SECRET: "e2e-secret",
  DEMO_EMAIL: "owner@paypilot.demo", DEMO_PASSWORD: "e2e-demo-password", LLM_API_KEY: "", LLM_MODEL: "" };

export default defineConfig({
  testDir: "e2e",
  timeout: 60_000,
  workers: 1,  // one shared database
  use: { baseURL: "http://localhost:5199", trace: "retain-on-failure" },
  webServer: [
    { command: `${py} seed.py && ${py} -m uvicorn app.main:app --port 8765`, cwd: "../backend", url: "http://localhost:8765/health", env, reuseExistingServer: false },
    { command: "npx vite --port 5199 --strictPort", url: "http://localhost:5199", env: { VITE_API_TARGET: "http://localhost:8765" }, reuseExistingServer: false },
  ],
});
