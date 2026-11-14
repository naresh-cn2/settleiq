const fs = require('fs');
const content = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const lines = content.split('\n');
const line444 = lines[443];
const line445 = lines[444];
const combined = line444 + '\n' + line445;
console.log('Combined length:', combined.length);
for (let i = 0; i < combined.length; i++) {
  console.log((i+1) + ': ' + combined[i]);