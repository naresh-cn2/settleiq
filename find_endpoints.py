import re

with open('C:/Users/nares/Workspace/settleiq/settleiq_frontend.js', 'rb') as f:
    c = f.read()
print(f'Size: {len(c)} bytes')
text = c.decode('utf-8', errors='replace')

endpoints = re.findall(r'["\'](/v1[^"\']*)["\']', text)
for ep in sorted(set(endpoints))[:50]:
    print(ep)
print(f"\nTotal unique v1 endpoints: {len(set(endpoints))}")