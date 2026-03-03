# fix_imports.py
import os
import sys

# Fix the admin.py file
admin_file = os.path.join('blog', 'admin.py')
if os.path.exists(admin_file):
    with open(admin_file, 'r') as f:
        content = f.read()

    # Remove the print statements at the end
    if 'print("✅ Admin panel ready!")' in content:
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if not (line.startswith('print(') and 'Admin panel ready' in line) and \
                    not (line.startswith('print(') and 'Visit:' in line):
                new_lines.append(line)

        with open(admin_file, 'w') as f:
            f.write('\n'.join(new_lines))
        print("✅ Fixed admin.py file")