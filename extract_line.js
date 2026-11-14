const fs = require('fs');
const lines = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8').split('\n');
const targetLine = 444; // 1-based
const line = lines[targetLine-1]; // zero-based index
console.log('Line ' + targetLine + ': [' + line + ']');
const len = line.length;
console.log('Length: ' + len);
for (let i = 0; i < len; i++) {
  const ch = line[i];
  if (ch !== ' ') {
    console.log('First non-space at position ' + (i+1) + ':', ch);
    break;
  }
}