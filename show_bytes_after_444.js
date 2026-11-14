const fs = require('fs');
const content = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const lines = content.split('\n');
const line444 = lines[443];
const line445 = lines[444];
const after444 = line444 + '\n' + line445; // this is what we think
// Let's get the actual bytes after line444 from the raw content
const raw = fs.readFileSync('frontend/scripts/verify_public_demo_e2e.mjs', 'utf8');
const idx444 = raw.indexOf(line444);
const idx445 = raw.indexOf(line445);
const before445 = raw.slice(idx444 + line444.length); // includes newline(s) up to line445 start
console.log('Before line445 (raw):', JSON.stringify(before445));