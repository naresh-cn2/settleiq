const fs = require('fs');
const content = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const lines = content.split('\n'); // split on \n only
const line444 = lines[443];
const line445 = lines[444];
console.log('Line 444 (raw):', JSON.stringify(line444));
console.log('Line 445 (raw):', JSON.stringify(line445));