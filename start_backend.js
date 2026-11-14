import { startBackend } from './frontend/scripts/verify_public_demo_e2e.mjs';

const demoSecret = 'SiMGOe7hrmLMe6SfYxjOcqrKq-6vxDf95r8-v1zcAtGUlV0ikGZKW-pLK8tu-mAD';
const apiKey = 'Dx37N3u6L7kA8Nq9BbQ9E47R1Yx623Zmf4ZRIcwhfQs';

const child = startBackend(8001, {
  SETTLEIQ_DEMO_SECRET: demoSecret,
  SETTLEIQ_API_KEY: apiKey,
});

console.log('Backend process started with PID:', child.pid);