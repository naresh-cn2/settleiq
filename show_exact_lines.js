const fs = require('fs');
const content = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const lines = content.split('\n');
const line444 = lines[443]; // 0-based index
const line445 = lines[444];
console.log('Line 444:', JSON.stringify(line444));
console.log('Line 445:', JSON.stringify(line445));