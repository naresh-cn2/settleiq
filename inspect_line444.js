const fs = require('fs');
const content = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const lines = content.split('\n');
const line444 = lines[443];
console.log('Full line 444:', JSON.stringify(line444));
const len = line444.length;
console.log('Length:', len);
for (let i = 0; i < len; i++) {
  const ch = line444[i];
  if (i > 30 && i < 60) { // show part after "return"
    console.log(i+1 + ': ' + ch);
  }
}