const fs = require('fs');
const content = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const lines = content.split('\n');
const targetLine = 445;
console.log('Line ' + targetLine + ':', JSON.stringify(lines[targetLine - 1]));