import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e',
  workers: 1,
  timeout: 90000,
  use: {
    baseURL: 'http://127.0.0.1:8765',
    browserName: 'chromium',
    launchOptions: {
      executablePath: process.env.CHROMIUM_BIN || '/usr/bin/chromium',
      args: ['--no-sandbox', '--disable-dev-shm-usage'],
    },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'bash ../../scripts/dev.sh',
    url: 'http://127.0.0.1:8765/api/health',
    timeout: 30000,
    reuseExistingServer: false,
    gracefulShutdown: { signal: 'SIGTERM', timeout: 5000 },
    env: { APP_DATA_DIR: `/tmp/whiteboard-e2e-${process.pid}`, APP_PORT: '8765' },
  },
});
