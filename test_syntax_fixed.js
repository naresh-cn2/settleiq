const fs = require('fs');
const content = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const lines = content.split('\n');
let errorCount = 0;
for (let i = 0; i < lines.length; i++) {
  try {
    new Function(lines[i]);
  } catch (e) {
    console.error('Syntax error at line ' + (i+1) + ':', e.message);
    errorCount++;
  }
}
console.log('Total syntax errors:', errorCount);