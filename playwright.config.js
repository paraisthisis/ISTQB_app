import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  retries: 1,
  use: {
    baseURL: 'http://localhost:5050',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      // Flask backend (local app)
      command: 'python3 backend/app.py',
      url: 'http://localhost:5050',
      reuseExistingServer: true,
      timeout: 15000,
    },
    {
      // GitHub Pages simulation: static frontend under /ISTQB_app/, no backend
      command: 'python3 ingestion/export_static.py && python3 tests/static_server.py 5051',
      url: 'http://localhost:5051/ISTQB_app/',
      reuseExistingServer: true,
      timeout: 15000,
    },
  ],
});
