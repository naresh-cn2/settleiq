const fs = require('fs');
const lines = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8').split('\n');
lines.forEach((line, i) => {
  if (i >= 435 && i <= 449) {
    console.log((i+1) + ': ' + line);
  }
});