const fs = require('fs');
const lines = fs.readFileSync('start_fastapi.mjs', 'utf8').split('\n');
for (let i = 439; i <= 449; i++) {
  console.log((i+1) + ': ' + lines[i]);
}