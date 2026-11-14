const s = "    return 'invalid token rejected, cleared, and explaned'\n  }";
let count = 0;
for (let i = 0; i < s.length; i++) {
  count++;
  // console.log(i+1 + ': ' + s[i]);
}
console.log('Combined length:', count);