import * as mod from './frontend/scripts/verify_public_demo_e2e.mjs';

const demoSecret = 'SiMGOe7hrmLMe6SfYxjOcqrKq-6vxDf95r8-v1zcAtGUlV0ikGZKW-pLK8tu-mAD';
const apiKey = 'Dx37N3u6L7kA8Nq9BbQ9E47R1Yx623Zmf4ZRIcwhfQs';

const child = mod.startBackend(8001, {
  SETTLEIQ_DEMO_SECRET: demoSecret,
  SETTLEIQ_API_KEY: apiKey,
});

console.log('Backend process started with PID:', child.pid);

// Wait for health endpoint to be ready
const checkHealth = async () => {
  const urls = [
    'http://127.0.0.1:8001/health',
    'http://127.0.0.1:8001/v1/health',
    'http://127.0.0.1:8001/'
  ];
  for (const url of urls) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        console.log(`Backend is ready (${url})`);
        return true;
      }
    } catch (error) {
      // ignore
    }
  }
  return false;
};

const timeoutMs = 30000; // 30 seconds
const intervalMs = 1000;
let elapsed = 0;

while (elapsed < timeoutMs) {
  const ready = await checkHealth();
  if (ready) {
    console.log('SUCCESS: Backend is ready');
    process.exit(0);
  }
  await new Promise(resolve => setTimeout(resolve, intervalMs));
  elapsed += intervalMs;
}

console.error('ERROR: Backend failed to become ready in time');
process.exit(1);