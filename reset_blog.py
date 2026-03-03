# reset_project.py
import os
import sys
import django
import shutil

# Add the project to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_core.settings')
django.setup()

from django.db import connection

print("=" * 50)
print("RESETTING BLOG PROJECT")
print("=" * 50)

# Option 1: Delete and recreate database
db_path = 'db.sqlite3'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✓ Deleted database: {db_path}")

# Delete migrations except __init__.py
migrations_dir = 'blog/migrations'
if os.path.exists(migrations_dir):
    for item in os.listdir(migrations_dir):
        if item != '__init__.py' and item.endswith('.py'):
            os.remove(os.path.join(migrations_dir, item))
    print(f"✓ Cleared migrations in {migrations_dir}")

# Delete __pycache__ directories
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        shutil.rmtree(os.path.join(root, '__pycache__'))
print("✓ Cleared __pycache__ directories")

print("\nNow run these commands:")
print("1. python manage.py makemigrations")
print("2. python manage.py migrate")
print("3. python manage.py createsuperuser")
print("4. python manage.py populate_blog")
print("5. python manage.py runserver")







