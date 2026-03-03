# revert_to_original.py
import os
import shutil


def revert_to_original():
    print("🔄 Reverting to original working code...")

    # 1. Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # 2. Create media directories
    media_dirs = ['media', 'media/blog_images', 'static']
    for dir_path in media_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    print("✅ Directories created")

    # 3. Update requirements.txt with original dependencies
    original_requirements = """Django==6.0.1
django-taggit==6.1.0
django-crispy-forms==2.5
crispy-bootstrap5==2025.6
Pillow==12.1.0
whitenoise==6.11.0
gunicorn==23.0.0
feedparser==6.0.11
beautifulsoup4==4.12.3
requests==2.32.3"""

    with open('requirements.txt', 'w') as f:
        f.write(original_requirements)

    print("✅ requirements.txt restored")

    print("\n🎉 Original setup restored!")
    print("\nRun these commands:")
    print("1. pip install -r requirements.txt")
    print("2. python manage.py migrate")
    print("3. python manage.py createsuperuser")
    print("4. python manage.py populate_blog")
    print("5. python manage.py runserver")
    print("\n⚠️  Use Firefox to avoid HSTS issues:")
    print("   http://localhost:8000")


if __name__ == "__main__":
    revert_to_original()