const fs = require('fs');
const content = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const lines = content.split('\n');
const line444 = lines[443];
console.log('Line 444 length:', line444.length);
console.log('Line 444 (with quotes):', JSON.stringify(line444));