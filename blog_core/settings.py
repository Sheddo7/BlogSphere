# blog_core/settings.py - RAILWAY PRODUCTION VERSION
import os
import dj_database_url
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/')

# --- Security ---
SECRET_KEY = os.environ['SECRET_KEY']
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['blogsphere.up.railway.app' 'blogsphere.ng', 'www.blogsphere.ng',]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'storages',
    'blog',
    'accounts',
    'taggit',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_apscheduler',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'blog_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'blog.context_processors.categories_processor',
                'blog.context_processors.latest_posts_processor',
                'blog.context_processors.seo_defaults',
            ],
        },
    },
]

WSGI_APPLICATION = 'blog_core.wsgi.application'

# --- Database ---
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# --- Static and Media Files ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# --- Supabase S3 Credentials ---
AWS_ACCESS_KEY_ID = os.environ.get('SUPABASE_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('SUPABASE_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('SUPABASE_BUCKET')
AWS_S3_ENDPOINT_URL = "https://oqqrptqnairmerdfbdgi.supabase.co/storage/v1/s3"
AWS_S3_REGION_NAME = "eu-west-1"
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "public-read"
AWS_QUERYSTRING_AUTH = False
AWS_S3_ADDRESSING_STYLE = "path"
AWS_S3_CUSTOM_DOMAIN = "oqqrptqnairmerdfbdgi.supabase.co/storage/v1/object/public/media"
MEDIA_URL = "https://oqqrptqnairmerdfbdgi.supabase.co/storage/v1/object/public/media/"

# --- Crispy Forms ---
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# --- Auth ---
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# --- NewsAPI ---
NEWS_API_KEY = os.environ.get('NEWS_API_KEY', '')

# --- APScheduler ---
APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"
APSCHEDULER_RUN_NOW_TIMEOUT = 25

CSRF_TRUSTED_ORIGINS = [
    'https://blogsphere.ng',
    'https://www.blogsphere.ng',
    'https://blogsphere.up.railway.app',
]

# Google Analytics
GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', '')

# Contact Form Email
CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL', 'info@blogsphere.ng')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@blogsphere.ng')

# Email Backend (development - prints to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Site Configuration
SITE_DOMAIN = os.environ.get('SITE_DOMAIN', 'blogsphere.ng')
SITE_NAME = 'BlogSphere'

# Social Media
TWITTER_HANDLE = os.environ.get('TWITTER_HANDLE', '@BlogSphereNG')