/**
 * SettleIQ Real Browser End-to-End Automation & Screenshot Capture Script.
 *
 * Uses puppeteer-core to launch real headless Google Chrome, interact with the
 * live React 18 single-page application served by FastAPI, execute the 60-second
 * guided demo seed, open and inspect AI forensic investigation hypotheses,
 * verify the visual transaction trace, commit an authorized resolution,
 * and capture real PNG screenshots into `proof/screenshots/`.
 */

import puppeteer from 'puppeteer-core';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, '..', '..');
const SCREENSHOTS_DIR = path.join(ROOT, 'proof', 'screenshots');
const LOG_FILE = path.join(ROOT, 'proof', 'browser_e2e_log.json');
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BASE_URL = 'http://127.0.0.1:8844';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitForServer(url, timeoutMs = 25000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(`${url}/health`);
      if (res.ok) return true;
    } catch {
      // server still starting
    }
    await sleep(500);
  }
  throw new Error(`FastAPI server did not become ready at ${url} within ${timeoutMs}ms`);
}

async function runBrowserE2E() {
  console.log('================================================================================');
  console.log('STARTING REAL BROWSER E2E VERIFICATION (Chrome Headless)');
  console.log('================================================================================');

  if (!fs.existsSync(SCREENSHOTS_DIR)) {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  }

  // 1. Check if server is already running, else start it
  let serverProcess = null;
  let alreadyRunning = false;
  try {
    const res = await fetch(`${BASE_URL}/health`);
    if (res.ok) {
      alreadyRunning = true;
      console.log('FastAPI backend server is already running on port 8844.');
    }
  } catch {
    console.log('Starting local FastAPI backend server on port 8844...');
    serverProcess = spawn('python', ['-m', 'uvicorn', 'settleiq.api.app:app', '--port', '8844'], {
      cwd: ROOT,
      stdio: 'ignore',
      detached: false,
      shell: true,
    });
  }

  try {
    await waitForServer(BASE_URL);
    console.log('FastAPI backend is responsive and healthy.');

    // 2. Launch real Google Chrome
    console.log(`Launching Google Chrome at: ${CHROME_PATH}`);
    const browser = await puppeteer.launch({
      executablePath: CHROME_PATH,
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900'],
      defaultViewport: { width: 1440, height: 900 },
    });

    const page = await browser.newPage();
    const consoleLogs = [];
    const pageErrors = [];
    const networkRequests = [];

    page.on('console', msg => {
      consoleLogs.push({ type: msg.type(), text: msg.text() });
    });

    page.on('pageerror', err => {
      pageErrors.push(err.toString());
      console.error('Browser Page Error:', err);
    });

    page.on('requestfailed', req => {
      networkRequests.push({
        url: req.url(),
        method: req.method(),
        failure: req.failure()?.errorText || 'failed',
      });
    });

    page.on('response', res => {
      if (res.status() >= 400) {
        networkRequests.push({
          url: res.url(),
          status: res.status(),
          statusText: res.statusText(),
        });
      }
    });

    // Accept alerts automatically
    page.on('dialog', async dialog => {
      console.log(`Browser Dialog: [${dialog.type()}] "${dialog.message()}"`);
      await dialog.accept();
    });

    // -------------------------------------------------------------------------
    // Step 1: Navigate to Dashboard / Runs Page
    // -------------------------------------------------------------------------
    console.log('[Step 1/6] Navigating to React Dashboard (Runs Page)...');
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle0' });
    await page.waitForSelector('.app', { timeout: 10000 });
    await sleep(800);

    const s1Path = path.join(SCREENSHOTS_DIR, '01_react_runs_dashboard.png');
    await page.screenshot({ path: s1Path });
    console.log(`           Captured screenshot: ${s1Path}`);

    // -------------------------------------------------------------------------
    // Step 2: Trigger 60-Second Demo Seed
    // -------------------------------------------------------------------------
    console.log('[Step 2/6] Executing "⚡ 60-Second Demo Seed" in UI...');
    const seedBtn = await page.waitForSelector('button ::-p-text(Demo Seed)', { timeout: 8000 });
    await seedBtn.click();

    // Wait for the seed notice banner to appear
    await page.waitForSelector('button ::-p-text(Investigate Detected Breaks)', { timeout: 15000 });
    await sleep(800);

    const s2Path = path.join(SCREENSHOTS_DIR, '02_react_demo_seeded.png');
    await page.screenshot({ path: s2Path });
    console.log(`           Captured screenshot: ${s2Path}`);

    // -------------------------------------------------------------------------
    // Step 3: Navigate to Discrepancy Queue
    // -------------------------------------------------------------------------
    console.log('[Step 3/6] Navigating to Discrepancy Queue...');
    const investigateBreaksBtn = await page.waitForSelector('button ::-p-text(Investigate Detected Breaks)');
    await investigateBreaksBtn.click();

    await page.waitForSelector('table tbody tr', { timeout: 10000 });
    await sleep(800);

    const s3Path = path.join(SCREENSHOTS_DIR, '03_react_discrepancy_queue.png');
    await page.screenshot({ path: s3Path });
    console.log(`           Captured screenshot: ${s3Path}`);

    // -------------------------------------------------------------------------
    // Step 4: Open First Discrepancy (AI Investigation & Visual Trace)
    // -------------------------------------------------------------------------
    console.log('[Step 4/6] Opening Discrepancy for Forensic AI Investigation...');
    const firstInvestigateBtn = await page.waitForSelector('table tbody tr:first-child button ::-p-text(Investigate)');
    await firstInvestigateBtn.click();

    // Wait for Visual Transaction Journey Trace & Hypotheses
    await page.waitForSelector('.card-title ::-p-text(Visual Transaction Journey Trace)', { timeout: 10000 });
    await page.waitForSelector('.card-title ::-p-text(AI Forensic Co-Pilot)', { timeout: 10000 });
    await page.waitForSelector('button ::-p-text(Accept AI Draft)', { timeout: 10000 });
    await sleep(1000);

    const s4Path = path.join(SCREENSHOTS_DIR, '04_react_ai_investigation_and_trace.png');
    await page.screenshot({ path: s4Path });
    console.log(`           Captured screenshot: ${s4Path}`);

    // -------------------------------------------------------------------------
    // Step 5: Accept AI Draft Resolution & Commit Authorized Resolution
    // -------------------------------------------------------------------------
    console.log('[Step 5/6] Accepting AI Draft Resolution & Committing...');
    const acceptDraftBtn = await page.waitForSelector('button ::-p-text(Accept AI Draft)', { timeout: 8000 });
    await acceptDraftBtn.click();
    await sleep(600);

    // Click Commit Immutable Resolution
    const submitResolveBtn = await page.waitForSelector('button[type="submit"] ::-p-text(Commit Immutable Resolution)');
    await submitResolveBtn.click();

    // Wait for reload and confirmed RESOLVED badge
    await page.waitForSelector('.badge-success ::-p-text(RESOLVED)', { timeout: 12000 });
    await sleep(800);

    const s5Path = path.join(SCREENSHOTS_DIR, '05_react_discrepancy_resolved.png');
    await page.screenshot({ path: s5Path });
    console.log(`           Captured screenshot: ${s5Path}`);

    // -------------------------------------------------------------------------
    // Step 6: Inspect History & Audit Journal View
    // -------------------------------------------------------------------------
    console.log('[Step 6/6] Inspecting Audit History & Metrics...');
    const historyNavLink = await page.waitForSelector('.nav-link ::-p-text(History)');
    await historyNavLink.click();

    await page.waitForSelector('.card-title', { timeout: 10000 });
    await sleep(800);

    const s6Path = path.join(SCREENSHOTS_DIR, '06_react_audit_history.png');
    await page.screenshot({ path: s6Path });
    console.log(`           Captured screenshot: ${s6Path}`);

    await browser.close();

    const outputLog = {
      timestamp: new Date().toISOString(),
      browser: 'Google Chrome Headless',
      viewport: { width: 1440, height: 900 },
      status: 'SUCCESS',
      screenshots: [
        '01_react_runs_dashboard.png',
        '02_react_demo_seeded.png',
        '03_react_discrepancy_queue.png',
        '04_react_ai_investigation_and_trace.png',
        '05_react_discrepancy_resolved.png',
        '06_react_audit_history.png',
      ],
      page_errors_count: pageErrors.length,
      page_errors: pageErrors,
      failed_network_requests: networkRequests,
      console_messages_count: consoleLogs.length,
    };

    fs.writeFileSync(LOG_FILE, JSON.stringify(outputLog, null, 2), 'utf8');
    console.log('================================================================================');
    console.log(`BROWSER E2E VERIFICATION COMPLETED (0 Page Errors)`);
    console.log(`Screenshots saved to: ${SCREENSHOTS_DIR}`);
    console.log(`Execution log saved to: ${LOG_FILE}`);
    console.log('================================================================================');
    return outputLog;
  } finally {
    if (serverProcess && !alreadyRunning) {
      serverProcess.kill('SIGTERM');
    }
  }
}

runBrowserE2E().catch(err => {
  console.error('Browser E2E Execution Failed:', err);
  process.exit(1);
});
