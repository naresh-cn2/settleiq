const fs = require('fs');
const content = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const lines = content.split('\n');
const line444 = lines[443];
const line445 = lines[444];
const after444 = line444 + '\n' + line445; // reconstruct with \n
console.log('Line 444:', JSON.stringify(line444));
console.log('Line 445:', JSON.stringify(line445));
console.log('Combined:', JSON.stringify(after444));