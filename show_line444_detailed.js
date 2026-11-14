const fs = require('fs');
const content = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const lines = content.split('\n');
const line444 = lines[443];
console.log('Line 444 length:', line444.length);
for (let i = 0; i < line444.length; i++) {
  const ch = line444[i];
  if (i > 30 && i < 60) {
    console.log((i+1) + ': ' + ch);
  }
}