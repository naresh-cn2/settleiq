const fs = require('fs');
const content = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const lines = content.split('\n'); // split on \n only
console.log('Number of lines:', lines.length);
for (let i = 440; i <= 450; i++) {
  const line = lines[i] || '(empty)';
  // Show line with visible \\r and \\n
  const escaped = line.replace(/\r/g, '\\r').replace(/\n/g, '\\n');
  console.log((i+1) + ': ' + JSON.stringify(line) + '  -->  ' + escaped);
}