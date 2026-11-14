const s = "'invalid token rejected, cleared, and explaned'";
let count = 0;
for (let i = 0; i < s.length; i++) {
  count++;
  // console.log(i+1 + ': ' + s[i]);
}
console.log('Quoted string length:', count);