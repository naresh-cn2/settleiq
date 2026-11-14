import os
import glob

def find_files_with_pattern(root_dir, pattern):
    matches = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(pattern):
                matches.append(os.path.join(dirpath, filename))
    return matches

# Search for files that might contain API routes
root_dir = 'C:\\Users\\nares\\Workspace\\settleiq\\src\\settleiq'
patterns = ['*.py', 'routers/*.py', 'api/*.py', 'endpoints/*.py', 'controllers/*.py']

for pattern in patterns:
    matches = find_files_with_pattern(root_dir, pattern)
    for match in matches:
        print(f'Found: {match}')