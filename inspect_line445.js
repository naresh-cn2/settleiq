const fs = require('fs');
const content = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const lines = content.split('\n');
const line445 = lines[444];
console.log('Full line 445:', JSON.stringify(line445));
const len = line445.length;
console.log('Length:', len);
for (let i = 0; i < len; i++) {
  const ch = line445[i];
  if (i > 0 && i < len) {
    console.log(i+1 + ': ' + ch);
  }
}