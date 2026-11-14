const fs = require('fs');
const lines = fs.readFileSync('start_fastapi.mjs', 'utf8').split('\n');
lines.forEach((line, i) => console.log((i+1) + ': ' + line));