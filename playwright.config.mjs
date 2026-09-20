import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 30000,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    locale: 'ja-JP',
    baseURL: 'http://127.0.0.1:4311',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: '.venv/bin/python -m src.local_server --port 4311',
    url: 'http://127.0.0.1:4311/health',
    env: { AUTH_DOMAIN: 'https://login.example.com' },
    reuseExistingServer: false,
    timeout: 30000,
  },
});
