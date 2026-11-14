const fs = require('fs');
const content = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const lines = content.split('\n');
const line445 = lines[444];
console.log('Line 445 (raw):', JSON.stringify(line445));