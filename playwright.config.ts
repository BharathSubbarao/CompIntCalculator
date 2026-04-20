import { defineConfig, devices } from "@playwright/test";

// Determine which browsers to skip based on environment
const skipBrowsers = new Set((process.env.SKIP_BROWSERS || "firefox,webkit").split(","));

const allProjects = [
  {
    name: "chromium",
    use: { ...devices["Desktop Chrome"] },
  },
  {
    name: "firefox",
    use: { ...devices["Desktop Firefox"] },
  },
  {
    name: "webkit",
    use: { ...devices["Desktop Safari"] },
  },
];

const projects = allProjects.filter((p) => !skipBrowsers.has(p.name));
const appPort = process.env.PLAYWRIGHT_APP_PORT || "8501";
const appUrl = `http://127.0.0.1:${appPort}`;

console.log(`Running tests on: ${projects.map((p) => p.name).join(", ")}`);

export default defineConfig({
  testDir: "./ui-tests",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  retries: 1,
  reporter: [
    ["list"],
    ["html", { open: "never" }],
    ["json", { outputFile: "playwright-results.json" }],
  ],
  use: {
    baseURL: appUrl,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: projects,
  webServer: {
    command: `python3 -m streamlit run app.py --server.headless true --server.port ${appPort} --logger.level=error`,
    url: appUrl,
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
