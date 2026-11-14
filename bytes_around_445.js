const fs = require('fs');
const data = fs.readFileSync('start_fastapi.mjs');
const lines = data.split('\n');
const targetLine = 445;
const start = Math.max(0, targetLine - 5);
const end = Math.min(data.length, targetLine + 5);
const slice = data.slice(start, end);
slice.forEach((line, i) => {
  const lineNumber = targetLine - 5 + i;
  console.log(lineNumber + ': ' + line);
});