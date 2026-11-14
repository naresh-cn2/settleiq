import { startBackend } from './frontend/scripts/verify_public_demo_e2e.mjs';

 // Generate random base64url strings
const demoSecret = require('crypto').randomBytes(48).toString('base64url').replace(/=/g, '');
const apiKey = require('crypto').randomBytes(32).toString('base64url').replace(/=/g, '');

console.log('Generating demoSecret:', demoSecret);
console.log('Generating apiKey:', apiKey);

 // Call startBackend with port 8001 and the generated secrets
const child = startBackend(8001, {
   SETTLEIQ_DEMO_SECRET: demoSecret,
   SETTLEIQ_API_KEY: apiKey,
 });

console.log('Backend process started with PID:', child.pid);

 // Wait for the backend to be ready by checking the root endpoint
const checkReady = async () => {
   try {
     const res = await fetch('http://127.0.0.1:8001/');
     if (res.ok) {
       console.log('Backend is ready!');
       return true;
     }
     return false;
   } catch (err) {
     return false;
   }
 };

 // Poll for readiness
const timeoutMs = 30000; // 30 seconds
const intervalMs = 1000;
let elapsed = 0;

while (elapsed < timeoutMs) {
   const ready = await checkReady();
   if (ready) {
     console.log('SUCCESS: Backend is ready on port 8001');
     process.exit(0);
   }
   await new Promise(resolve => setTimeout(resolve, intervalMs));
   elapsed += intervalMs;
 }

console.error('ERROR: Backend failed to become ready in time');
process.exit(1);