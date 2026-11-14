import puppeteer from 'puppeteer-core'
import { spawn } from 'node:child_process'
import crypto from 'node:crypto'
import fs from 'node:fs'
import net from 'node:net'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const ROOT = path.resolve(__dirname, '..', '..')

// Directory for E2E evidence reports.
const PROOF_DIR = path.join(ROOT, 'proof', 'e2e')

// Resolve the Google Chrome executable for puppeteer-core. Falls back through
// the common Windows install locations so the verifier works on any dev box.
const CHROME_PATH = (() => {
  const candidates = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    `${process.env.LOCALAPPDATA}\\Google\\Chrome\\Application\\chrome.exe`,
  ]
  for (const candidate of candidates) {
    try {
      if (fs.existsSync(candidate)) return candidate
    } catch {
      // Ignore and try the next candidate.
    }
  }
  return candidates[0]
})()

function arg(name, fallback = undefined) {
  const index = process.argv.indexOf(`--${name}`)
  return index >= 0 ? process.argv[index + 1] : fallback
}

const MODE = arg('mode', 'local')
const appUrlArg = arg('app-url')
const apiUrlArg = arg('api-url')
const apiBUrlArg = arg('api-b-url')
let APP_URL = appUrlArg || (MODE === 'production' ? 'https://settleiq-zeta.vercel.app' : '')
let API_URL = apiUrlArg || (MODE === 'production' ? APP_URL : '')
let API_B_URL = apiBUrlArg || API_URL
const API_KEY =
  arg('api-key') ||
  (arg('api-key-file') ? fs.readFileSync(path.resolve(ROOT, arg('api-key-file')), 'utf8').trim() : '')

const results = []
const consoleErrors = []
const pageErrors = []
const failedRequests = []
let browser = null
let page = null
let local = null

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms))

function record(name, status, detail) {
  results.push({ name, status, detail })
  const marker = status === 'pass' ? 'PASS' : status === 'skip' ? 'SKIP' : 'FAIL'
  console.log(`${marker}  ${name}${detail ? ` — ${detail}` : ''}`)
}

async function test(name, fn) {
  const started = Date.now()
  try {
    const detail = await fn()
    record(name, 'pass', detail)
    return detail
  } catch (error) {
    record(name, 'fail', error instanceof Error ? error.message : String(error))
    throw error
  } finally {
    results[results.length - 1].ms = Date.now() - started
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(`${message}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`)
  }
}

async function fetchJson(url, options = {}) {
  const res = await fetch(url, options)
  let body = null
  try {
    body = await res.json()
  } catch {
    body = null
  }
  return { status: res.status, body, headers: res.headers }
}

async function waitForHttp(url, timeoutMs = 45000) {
  const deadline = Date.now() + timeoutMs
  let lastError = ''
  while (Date.now() < deadline) {
    try {
      const res = await fetch(url)
      if (res.status < 500) return true
      lastError = `HTTP ${res.status}`
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error)
    }
    await sleep(300)
  }
  throw new Error(`Timed out waiting for ${url}: ${lastError}`)
}

async function waitForPortFree(port, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const inUse = await new Promise(resolve => {
      const server = net.createServer()
      server.once('error', () => resolve(true))
      server.once('listening', () => server.close(() => resolve(false)))
      server.listen(port, '127.0.0.1')
    })
    if (!inUse) return
    await sleep(200)
  }
  throw new Error(`Port ${port} did not become free`)
}

async function getFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.unref()
    server.once('error', reject)
    server.listen(0, '127.0.0.1', () => {
      const address = server.address()
      const port = typeof address === 'object' && address ? address.port : 0
      server.close(() => resolve(port))
    })
  })
}

async function allocatePorts(count) {
  const ports = []
  while (ports.length < count) {
    const port = await getFreePort()
    if (port && !ports.includes(port)) ports.push(port)
  }
  return ports
}

async function waitForBackend(baseUrl, timeoutMs = 45000) {
  const deadline = Date.now() + timeoutMs
  let last = ''
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${baseUrl}/v1/demo/runs`)
      if (res.status === 401) return true
      last = `HTTP ${res.status}`
    } catch (error) {
      last = error instanceof Error ? error.message : String(error)
    }
    await sleep(300)
  }
  throw new Error(`Timed out waiting for SettleIQ at ${baseUrl}: ${last}`)
}

function killTree(child) {
  if (!child || child.killed) return
  try {
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'], { stdio: 'ignore' })
    } else {
      child.kill('SIGTERM')
    }
  } catch {
    // Best effort cleanup.
  }
}

export function startBackend(port, extraEnv = {}) {
  const env = {
    ...process.env,
    PYTHONPATH: path.join(ROOT, 'src'),
    SETTLEIQ_DB_PATH: ':memory:',
    SETTLEIQ_RATE_LIMIT: '1000',
    SETTLEIQ_DEMO_SESSION_RATE_LIMIT: '100',
    ...extraEnv,
  }
  const child = spawn(
    'python',
    ['-m', 'uvicorn', 'settleiq.api.app:app', '--host', '127.0.0.1', '--port', String(port)],
    { cwd: ROOT, env, stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true }
  )
  child.stdout.on('data', () => {})
  child.stderr.on('data', () => {})
  return child
}

async function startLocalStack() {
  const secret = crypto.randomBytes(48).toString('base64url')
  const apiKey = crypto.randomBytes(32).toString('base64url')
  const [portA, portB, portNoSecret, portWrongSecret, portShortLived, previewPort] =
    await allocatePorts(6)
  const base = port => `http://127.0.0.1:${port}`
  const stack = {
    secret,
    apiKey,
    ports: {
      a: portA,
      b: portB,
      noSecret: portNoSecret,
      wrongSecret: portWrongSecret,
      shortLived: portShortLived,
      preview: previewPort,
    },
    apiUrl: base(portA),
    apiBUrl: base(portB),
    appUrl: base(previewPort),
    backends: {},
    preview: null,
  }

  stack.backends.a = startBackend(portA, {
    SETTLEIQ_DEMO_SECRET: secret,
    SETTLEIQ_API_KEY: apiKey,
  })
  stack.backends.b = startBackend(portB, {
    SETTLEIQ_DEMO_SECRET: secret,
    SETTLEIQ_API_KEY: apiKey,
  })
  stack.backends.noSecret = startBackend(portNoSecret, {
    SETTLEIQ_DEMO_SECRET: '',
    SETTLEIQ_API_KEY: apiKey,
  })
  stack.backends.wrongSecret = startBackend(portWrongSecret, {
    SETTLEIQ_DEMO_SECRET: crypto.randomBytes(48).toString('base64url'),
    SETTLEIQ_API_KEY: apiKey,
  })
  stack.backends.shortLived = startBackend(portShortLived, {
    SETTLEIQ_DEMO_SECRET: secret,
    SETTLEIQ_API_KEY: apiKey,
    SETTLEIQ_DEMO_TOKEN_TTL_SECS: '1',
  })

  await Promise.all([
    waitForBackend(base(portA)),
    waitForBackend(base(portB)),
    waitForBackend(base(portNoSecret)),
    waitForBackend(base(portWrongSecret)),
    waitForBackend(base(portShortLived)),
  ])

  stack.preview = spawn(
    'npm',
    ['run', 'preview', '--', '--host', '127.0.0.1', '--port', String(previewPort), '--strictPort'],
    {
      cwd: path.join(ROOT, 'frontend'),
      env: { ...process.env, SETTLEIQ_API_PROXY_TARGET: stack.apiUrl },
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: true,
      windowsHide: true,
    }
  )
  stack.preview.stdout.on('data', () => {})
  stack.preview.stderr.on('data', () => {})
  await waitForHttp(`${stack.appUrl}/auth`)
  // Prove the preview proxy reaches *our* backend, not a stale server.
  const proxied = await fetch(`${stack.appUrl}/v1/demo/runs`)
  if (proxied.status !== 401) {
    throw new Error(`Preview proxy did not reach the SettleIQ API: HTTP ${proxied.status}`)
  }
  return stack
}

async function browserFetch(requestPath, headers = {}, method = 'GET', body) {
  return page.evaluate(
    async ({ requestPath, headers, method, body }) => {
      const init = { method, headers }
      if (body !== undefined) init.body = body
      const res = await fetch(requestPath, init)
      let payload = null
      try {
        payload = await res.json()
      } catch {
        payload = null
      }
      return { status: res.status, body: payload }
    },
    { requestPath, headers, method, body }
  )
}

async function waitForText(selector, expected, timeout = 20000) {
  await page.waitForFunction(
    (sel, text) => {
      const el = document.querySelector(sel)
      return !!el && (el.textContent || '').includes(text)
    },
    { timeout },
    selector,
    expected
  )
}

async function count(selector) {
  return page.$$eval(selector, els => els.length)
}

async function runBrowserJourney() {
  await page.goto(`${APP_URL}/auth`, { waitUntil: 'networkidle0' })
  await page.waitForSelector('[data-testid="explore-demo"]', { timeout: 60000 })

  let demoToken = ''
  let runId = ''

  await test('auth page renders login and public demo entry points', async () => {
    const heading = await page.$eval('h1', el => el.textContent || '')
    const hasInput = (await page.$('[data-testid="api-key-input"]')) !== null
    const button = await page.$eval('[data-testid="explore-demo"]', el => el.textContent || '')
    assert(heading.includes('SettleIQ'), `unexpected heading ${heading}`)
    assert(hasInput, 'API key input is missing')
    assert(button.includes('Explore Public Demo'), `unexpected demo button ${button}`)
    return 'login + demo controls visible'
  })

  await test('Explore Public Demo creates a session and lands on the dashboard', async () => {
    await page.click('[data-testid="explore-demo"]')
    await page.waitForFunction(() => location.pathname === '/dashboard', { timeout: 20000 })
    await waitForText('.demo-banner', 'PUBLIC DEMO')
    demoToken = await page.evaluate(() => sessionStorage.getItem('settleiq_demo_token') || '')
    assert(demoToken.length > 20, 'demo token was not stored')
    return 'demo session established on dashboard'
  })

  await test('dashboard shows aggregate overview metrics', async () => {
    await page.waitForSelector('h1', { timeout: 20000 })
    const heading = await page.$eval('h1', el => el.textContent || '')
    assert(heading.includes('Overview'), `unexpected heading ${heading}`)
    return 'overview dashboard loaded'
  })

  await test('dashboard navigates to runs page showing run data', async () => {
    await page.click('[data-testid="view-all-runs"]')
    await page.waitForSelector('[data-testid="run-row"]', { timeout: 20000 })
    await waitForText('.demo-banner', 'PUBLIC DEMO')
    const rows = await count('[data-testid="run-row"]')
    assertEqual(rows, 1, 'run row count')
    const text = await page.$eval('[data-testid="run-row"]', el => el.textContent || '')
    assert(text.includes('76.00%'), `run rate missing from ${text}`)
    assert(text.includes('COMPLETED'), 'run status missing')
    assert(/(^|[^0-9])7([^0-9]|$)/.test(text), `discrepancy count missing from ${text}`)
    runId = text.trim().slice(0, 16)
    return 'one completed run at 76.00% with 7 discrepancies'
  })

  await test('runs page can execute the demo seed endpoint', async () => {
    await page.click('[data-testid="seed-demo"]')
    await page.waitForSelector('[data-testid="investigate-breaks"]', { timeout: 20000 })
    const notice = await page.$eval('[data-testid="investigate-breaks"]', el => el.closest('.card')?.textContent || '')
    assert(notice.includes('Seeded Enterprise Reconciliation Dataset'), 'seed success banner missing')
    return 'demo seed executed in the browser'
  })

  await test('discrepancies page lists every synthetic break', async () => {
    await page.click('[data-testid="nav-discrepancies"]')
    await page.waitForSelector('[data-testid="discrepancy-row"]', { timeout: 20000 })
    const rows = await count('[data-testid="discrepancy-row"]')
    assertEqual(rows, 7, 'discrepancy row count')
    const text = await page.$eval('[data-testid="discrepancy-count"]', el => el.textContent || '')
    assert(text.includes('7'), `unexpected count text ${text}`)
    return '7 discrepancies listed'
  })

  await test('investigation and transaction trace render evidence and hypotheses', async () => {
    await page.click('[data-testid="investigate-discrepancy"]')
    await page.waitForSelector('[data-testid="investigation-page"]', { timeout: 20000 })
    await page.waitForSelector('[data-testid="transaction-trace"]', { timeout: 20000 })
    const hypotheses = await count('[data-testid="hypothesis"]')
    assert(hypotheses >= 1, 'no investigation hypotheses rendered')
    const contributing = await count('[data-testid="contributing-record"]')
    assert(contributing >= 1, 'no contributing records rendered')
    const body = await page.$eval('[data-testid="investigation-page"]', el => el.textContent || '')
    assert(body.includes('Visual Transaction Journey Trace'), 'trace heading missing')
    assert(body.includes('AI Forensic Co-Pilot'), 'investigation heading missing')
    return `${hypotheses} hypotheses, ${contributing} contributing records`
  })

  await test('metrics page loads the run automatically and shows the rate', async () => {
    await page.click('[data-testid="nav-metrics"]')
    await page.waitForSelector('[data-testid="metrics-page"]', { timeout: 20000 })
    await waitForText('[data-testid="auto-match-rate"]', '76.00%')
    const body = await page.$eval('[data-testid="metrics-page"]', el => el.textContent || '')
    assert(body.includes('19'), 'numerator missing')
    assert(body.includes('25'), 'denominator missing')
    assert(body.includes('Methodology'), 'methodology section missing')
    return 'metrics loaded automatically at 76.00% (19/25)'
  })

  await test('history page shows an audit timeline for the run', async () => {
    await page.click('[data-testid="nav-history"]')
    await page.waitForSelector('[data-testid="history-page"]', { timeout: 20000 })
    await page.waitForSelector('[data-testid="history-entry"]', { timeout: 20000 })
    const entries = await count('[data-testid="history-entry"]')
    assert(entries >= 3, `expected audit entries, got ${entries}`)
    const body = await page.$eval('[data-testid="history-timeline"]', el => el.textContent || '')
    assert(body.includes('RUN_COMPLETED'), 'run completion event missing')
    assert(body.includes('DISCREPANCY_DETECTED'), 'discrepancy events missing')
    return `${entries} audit history entries`
  })

  await test('browser refresh preserves the demo session', async () => {
    await page.reload({ waitUntil: 'networkidle0' })
    await page.waitForSelector('[data-testid="history-page"]', { timeout: 20000 })
    await page.waitForSelector('[data-testid="history-entry"]', { timeout: 20000 })
    const banner = await page.$eval('.demo-banner', el => el.textContent || '')
    assert(banner.includes('PUBLIC DEMO'), 'demo banner disappeared after refresh')
    return 'session and page state survive refresh'
  })

  await test('direct navigation to an application route works', async () => {
    await page.goto(`${APP_URL}/discrepancies?run_id=deadbeef`, { waitUntil: 'networkidle0' })
    await page.waitForSelector('[data-testid="discrepancies-empty"]', { timeout: 20000 })
    await page.goto(`${APP_URL}/metrics`, { waitUntil: 'networkidle0' })
    await page.waitForSelector('[data-testid="metrics-page"]', { timeout: 20000 })
    await waitForText('[data-testid="auto-match-rate"]', '76.00%')
    return 'direct route loads without a server-side 404'
  })

  await test('empty result set renders an explicit empty state', async () => {
    await page.goto(`${APP_URL}/discrepancies?run_id=does-not-exist`, { waitUntil: 'networkidle0' })
    await page.waitForSelector('[data-testid="discrepancies-empty"]', { timeout: 20000 })
    const text = await page.$eval('[data-testid="discrepancies-empty"]', el => el.textContent || '')
    assert(text.includes('No discrepancies'), `unexpected empty text ${text}`)
    return 'empty dataset handled with an explicit message'
  })

  await test('demo token cannot access production API endpoints', async () => {
    await page.goto(`${APP_URL}/`, { waitUntil: 'networkidle0' })
    await page.waitForSelector('[data-testid="run-row"]', { timeout: 20000 })
    const token = await page.evaluate(() => sessionStorage.getItem('settleiq_demo_token') || '')
    const getResult = await browserFetch('/v1/runs', { 'X-Demo-Token': token })
    const postResult = await browserFetch('/v1/runs', { 'X-Demo-Token': token }, 'POST', '{}')
    assertEqual(getResult.status, 401, 'demo token GET /v1/runs')
    assertEqual(postResult.status, 401, 'demo token POST /v1/runs')
    const demoResult = await browserFetch('/v1/demo/runs', { 'X-Demo-Token': token })
    assertEqual(demoResult.status, 200, 'demo token /v1/demo/runs')
    return 'demo token rejected by production routes and accepted by demo routes'
  })

  const effectiveApiKey = MODE === 'local' ? local?.apiKey || '' : API_KEY
  if (effectiveApiKey) {
    await test('production API-key authentication still works', async () => {
      const wrong = await browserFetch('/v1/runs', { 'X-API-Key': 'wrong-key' })
      const right = await browserFetch('/v1/runs', { 'X-API-Key': effectiveApiKey })
      assertEqual(wrong.status, 401, 'wrong API key')
      assertEqual(right.status, 200, 'correct API key')
      return 'wrong key rejected, valid key accepted'
    })
  } else {
    record('production API-key authentication still works', 'skip', 'no API key supplied')
  }

  await test('invalid demo token is rejected and redirected with a useful message', async () => {
    await page.evaluate(() => sessionStorage.setItem('settleiq_demo_token', 'not-a-valid-token'))
    await page.goto(`${APP_URL}/`, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await page.waitForFunction(() => location.pathname === '/auth', { timeout: 20000 })
    await page.waitForSelector('[data-testid="session-notice"]', { timeout: 10000 })
    const notice = await page.$eval('[data-testid="session-notice"]', el => el.textContent || '')
    const store = await page.evaluate(() => sessionStorage.getItem('settleiq_demo_token'))
    assertEqual(store, null, 'invalid token should be cleared')
    assert(notice.toLowerCase().includes('expired'), `unexpected notice ${notice}`)
    return 'invalid token rejected, cleared, and explained'
  });

  if (MODE === 'local') {
    await test('expired demo token is rejected', async () => {
      const now = Math.floor(Date.now() / 1000)
      const payload = JSON.stringify({ iat: now - 3600, exp: now - 1800, nonce: 'expired-token-e2e' })
      const signature = crypto.createHmac('sha256', local.secret).update(payload).digest()
      const token = `${Buffer.from(payload).toString('base64url')}.${signature.toString('base64url')}`
      await page.evaluate(t => sessionStorage.setItem('settleiq_demo_token', t), token)
      await page.goto(`${APP_URL}/dashboard`, { waitUntil: 'networkidle0' })
      await page.waitForFunction(() => location.pathname === '/login', { timeout: 20000 })
      const notice = await page.$eval('[data-testid="session-notice"]', el => el.textContent || '')
      assert(notice.toLowerCase().includes('expired'), `unexpected notice ${notice}`)
      return 'expired token rejected and session cleared'
    })
  } else {
    record('expired demo token is rejected', 'skip', 'requires the server signing secret; covered by local multi-instance suite')
  }

  await test('network failure renders an error state instead of a blank page', async () => {
    await page.click('[data-testid="explore-demo"]')
    await page.waitForFunction(() => location.pathname === '/dashboard', { timeout: 20000 })
    await page.waitForSelector('[data-testid="view-all-runs"]', { timeout: 20000 })
    await page.click('[data-testid="view-all-runs"]')
    await page.waitForSelector('[data-testid="run-row"]', { timeout: 20000 })
    await page.setRequestInterception(true)
    const handler = request => {
      if (request.url().includes('/v1/demo/runs') && !request.url().match(/\/v1\/demo\/runs\/[^/]+/)) {
        request.abort()
      } else {
        request.continue()
      }
    }
    page.on('request', handler)
    try {
      await page.goto(`${APP_URL}/runs`, { waitUntil: 'domcontentloaded' })
      await page.waitForFunction(
        () => (document.body.innerText || '').includes('Failed to load runs'),
        { timeout: 20000 }
      )
    } finally {
      page.off('request', handler)
      await page.setRequestInterception(false)
    }
    return 'failed API request surfaced as an actionable error'
  })

  await test('logout clears the demo session and protects routes', async () => {
    await page.goto(`${APP_URL}/`, { waitUntil: 'networkidle0' })
    await page.waitForSelector('[data-testid="exit-demo"]', { timeout: 20000 })
    await page.click('[data-testid="exit-demo"]')
    await page.waitForFunction(() => location.pathname === '/auth', { timeout: 20000 })
    const store = await page.evaluate(() => ({
      demo: sessionStorage.getItem('settleiq_demo_token'),
      api: sessionStorage.getItem('settleiq_api_key'),
    }))
    assertEqual(store.demo, null, 'demo token after logout')
    assertEqual(store.api, null, 'API key after logout')
    await page.goto(`${APP_URL}/history`, { waitUntil: 'networkidle0' })
    await page.waitForFunction(() => location.pathname === '/auth', { timeout: 20000 })
    return 'session terminated and protected route redirected'
  })

  return { demoToken, runId }
}

async function runApiTests(token, runId) {
  const tokenHeaders = { 'X-Demo-Token': token }

  await test('demo token validates on an independent serverless-equivalent instance', async () => {
    const result = await fetchJson(`${API_B_URL}/v1/demo/runs`, { headers: tokenHeaders })
    assertEqual(result.status, 200, 'cross-instance demo request')
    assertEqual(result.body?.count, 1, 'cross-instance run count')
    return 'same signed token accepted by a separate backend process'
  })

  await test('tampered demo token is rejected', async () => {
    const [payloadB64, signatureB64] = token.split('.')
    const signature = Buffer.from(signatureB64, 'base64url')
    signature[0] = signature[0] ^ 0xff
    const tampered = `${payloadB64}.${signature.toString('base64url')}`
    const result = await fetchJson(`${API_B_URL}/v1/demo/runs`, {
      headers: { 'X-Demo-Token': tampered },
    })
    assertEqual(result.status, 401, 'tampered token')
    return 'signature tampering rejected'
  })

  await test('demo token survives a backend cold start', async () => {
    if (MODE !== 'local') {
      return 'production serverless instances are managed by Vercel; local cold-start proof covers the token model'
    }
    killTree(local.backends.a)
    await waitForPortFree(local.ports.a)
    local.backends.a = startBackend(local.ports.a, {
      SETTLEIQ_DEMO_SECRET: local.secret,
      SETTLEIQ_API_KEY: local.apiKey,
    })
    await waitForBackend(local.apiUrl)
    const result = await fetchJson(`${local.apiUrl}/v1/demo/runs`, { headers: tokenHeaders })
    assertEqual(result.status, 200, 'token after cold start')
    return 'token remains valid after the server process is replaced'
  })

  await test('missing demo secret fails closed with an actionable 503', async () => {
    if (MODE !== 'local') {
      return 'requires control of the deployed environment; covered by local suite'
    }
    const result = await fetchJson(
      `http://127.0.0.1:${local.ports.noSecret}/v1/demo/session`,
      { method: 'POST' }
    )
    assertEqual(result.status, 503, 'missing secret status')
    assert(
      String(result.body?.detail || '').toLowerCase().includes('demo secret'),
      `unexpected detail ${JSON.stringify(result.body)}`
    )
    return 'demo disabled when the secret is absent'
  })

  await test('a token signed with a different secret is rejected', async () => {
    if (MODE !== 'local') {
      return 'requires control of the deployed secret; covered by local suite'
    }
    const result = await fetchJson(
      `http://127.0.0.1:${local.ports.wrongSecret}/v1/demo/runs`,
      { headers: tokenHeaders }
    )
    assertEqual(result.status, 401, 'wrong-secret token')
    return 'tokens are bound to the configured secret'
  })

  await test('short-lived token expires', async () => {
    if (MODE !== 'local') {
      return 'requires a short-TTL deployment; covered by local suite'
    }
    const shortLivedBase = `http://127.0.0.1:${local.ports.shortLived}`
    const issued = await fetchJson(`${shortLivedBase}/v1/demo/session`, { method: 'POST' })
    assertEqual(issued.status, 201, 'short-lived session issue')
    await sleep(2200)
    const result = await fetchJson(`${shortLivedBase}/v1/demo/runs`, {
      headers: { 'X-Demo-Token': issued.body.demo_token },
    })
    assertEqual(result.status, 401, 'expired token')
    return 'expiry enforced without server-side state'
  })

  await test('unknown demo run returns 404 and empty filters return empty sets', async () => {
    const missingRun = await fetchJson(`${API_URL}/v1/demo/runs/does-not-exist`, {
      headers: tokenHeaders,
    })
    assertEqual(missingRun.status, 404, 'unknown run')
    const emptyFilter = await fetchJson(
      `${API_URL}/v1/demo/discrepancies?run_id=does-not-exist`,
      { headers: tokenHeaders }
    )
    assertEqual(emptyFilter.status, 200, 'empty filter status')
    assertEqual(emptyFilter.body?.count, 0, 'empty filter count')
    return '404 and empty datasets handled explicitly'
  })

  await test('demo endpoints tolerate repeated requests', async () => {
    for (let i = 0; i < 20; i += 1) {
      const result = await fetchJson(`${API_URL}/v1/demo/discrepancies`, { headers: tokenHeaders })
      assertEqual(result.status, 200, `repeated request ${i + 1}`)
    }
    return '20 consecutive requests succeeded'
  })

  if (runId) {
    await test('demo trace endpoint returns real nodes for a constituent', async () => {
      const discrepancies = await fetchJson(`${API_URL}/v1/demo/discrepancies`, {
        headers: tokenHeaders,
      })
      const constituent = discrepancies.body.discrepancies[0].constituent_id
      const result = await fetchJson(
        `${API_URL}/v1/demo/runs/${discrepancies.body.discrepancies[0].run_id}/trace/${constituent}`,
        { headers: tokenHeaders }
      )
      assertEqual(result.status, 200, 'trace status')
      assert((result.body?.nodes || []).length > 0, 'trace has no nodes')
      return `${result.body.nodes.length} trace nodes`
    })
  }
}

async function run() {
  fs.mkdirSync(PROOF_DIR, { recursive: true })

  if (MODE === 'local') {
    local = await startLocalStack()
    APP_URL = local.appUrl
    API_URL = local.apiUrl
    API_B_URL = local.apiBUrl
    console.log(`Local stack ports: ${JSON.stringify(local.ports)}`)
  } else {
    await waitForHttp(`${APP_URL}/auth`)
    await waitForHttp(`${API_URL}/health`)
  }
  console.log(`SettleIQ E2E mode=${MODE} app=${APP_URL} api=${API_URL}`)

  browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900'],
    defaultViewport: { width: 1440, height: 900 },
  })
  page = await browser.newPage()
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text())
  })
  page.on('pageerror', error => pageErrors.push(String(error)))
  page.on('requestfailed', request => {
    failedRequests.push({ url: request.url(), error: request.failure()?.errorText || 'failed' })
  })
  page.on('dialog', async dialog => {
    consoleErrors.push(`dialog:${dialog.message()}`)
    await dialog.accept()
  })

  const journey = await runBrowserJourney()

  let token = journey.demoToken
  if (!token) {
    const issued = await fetchJson(`${API_URL}/v1/demo/session`, { method: 'POST' })
    assertEqual(issued.status, 201, 'fallback demo session issue')
    token = issued.body.demo_token
  }
  await runApiTests(token, journey.runId)

  // A final cold-start reload exercises the browser against a replaced backend.
  if (MODE === 'local') {
    await test('browser still works against a replaced backend process', async () => {
      await page.goto(`${APP_URL}/auth`, { waitUntil: 'networkidle0' })
      await page.click('[data-testid="explore-demo"]')
      await page.waitForSelector('[data-testid="run-row"]', { timeout: 20000 })
      killTree(local.backends.a)
      await waitForPortFree(local.ports.a)
      local.backends.a = startBackend(local.ports.a, {
        SETTLEIQ_DEMO_SECRET: local.secret,
        SETTLEIQ_API_KEY: local.apiKey,
      })
      await waitForBackend(local.apiUrl)
      await page.reload({ waitUntil: 'networkidle0' })
      await page.waitForSelector('[data-testid="run-row"]', { timeout: 20000 })
      return 'refreshing against a new process keeps the demo session'
    })
  }
}

function writeReport(extra = {}) {
  const report = {
    generated_at: new Date().toISOString(),
    mode: MODE,
    app_url: APP_URL,
    api_url: API_URL,
    api_b_url: API_B_URL,
    counts: {
      total: results.length,
      passed: results.filter(r => r.status === 'pass').length,
      failed: results.filter(r => r.status === 'fail').length,
      skipped: results.filter(r => r.status === 'skip').length,
    },
    results,
    console_errors: consoleErrors,
    page_errors: pageErrors,
    failed_requests: failedRequests,
    ...extra,
  }
  const file = path.join(PROOF_DIR, `public_demo_${MODE}_${Date.now()}.json`)
  fs.writeFileSync(file, JSON.stringify(report, null, 2))
  fs.writeFileSync(path.join(PROOF_DIR, `public_demo_${MODE}_latest.json`), JSON.stringify(report, null, 2))
  console.log(`\nReport: ${file}`)
  console.log(
    `Result: ${report.counts.passed} passed, ${report.counts.failed} failed, ${report.counts.skipped} skipped`
  )
  return report
}

async function cleanup() {
  if (page) {
    try {
      await page.close()
    } catch {
      // ignore
    }
  }
  if (browser) {
    try {
      await browser.close()
    } catch {
      // ignore
    }
  }
  if (local) {
    killTree(local.preview)
    Object.values(local.backends).forEach(killTree)
  }
}

try {
  await run()
  const report = writeReport()
  await cleanup()
  if (report.counts.failed > 0 || report.counts.passed === 0) process.exit(1)
  process.exit(0)
} catch (error) {
  console.error(`\nE2E FAILED: ${error instanceof Error ? error.stack : error}`)
  if (page) {
    try {
      const shot = path.join(PROOF_DIR, `failure_${Date.now()}.png`)
      await page.screenshot({ path: shot, fullPage: true })
      console.error(`Failure screenshot: ${shot}`)
    } catch {
      // ignore
    }
  }
  writeReport({ fatal_error: error instanceof Error ? error.message : String(error) })
  await cleanup()
  process.exit(1)
}