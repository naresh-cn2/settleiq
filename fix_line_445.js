const fs = require('fs');
const content = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const lines = content.split('\n');
const targetLine = 445;
lines[targetLine - 1] = '  });';
const newContent = lines.join('\n');
fs.writeFileSync('frontend/scripts/verify_public_demo_e2e.mjs', newContent);
console.log('Fixed line 445');