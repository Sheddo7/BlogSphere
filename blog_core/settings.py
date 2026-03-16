# blog_core/settings.py - RAILWAY PRODUCTION VERSION with Performance Optimizations
import os
import dj_database_url
from pathlib import Path

# Cloudinary imports for image CDN (add near top after pathlib)
import cloudinary
import cloudinary.uploader
import cloudinary.api

BASE_DIR = Path(__file__).resolve().parent.parent

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/')

# --- Security ---
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['blogsphere.up.railway.app']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    # Cloudinary (MUST be before staticfiles!)

    'cloudinary',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',

    # Third party
    'storages',
    'taggit',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_apscheduler',

    # Your apps
    'blog',
    'accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # Whitenoise for static files (after security)
    'whitenoise.middleware.WhiteNoiseMiddleware',

    # GZip compression (after security, before others)
    'django.middleware.gzip.GZipMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Custom performance/security middleware (add these last)
    'blog_core.middleware.SecurityHeadersMiddleware',
    'blog_core.middleware.CompressionMiddleware',
]

ROOT_URLCONF = 'blog_core.urls'

# Templates with caching in production
if not DEBUG:
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [BASE_DIR / 'templates'],
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
                'loaders': [
                    # Cached template loader (production only!)
                    ('django.template.loaders.cached.Loader', [
                        'django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader',
                    ]),
                ],
            },
        },
    ]
else:
    # Development template config (no caching)
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

# --- Database with connection pooling ---
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600                 # Keep connections alive for 10 minutes
        )
    }
    # Add additional database options
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# --- Static and Media Files with WhiteNoise & Cloudinary ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise settings for static files
WHITENOISE_MAX_AGE = 31536000                     # 1 year browser cache
WHITENOISE_AUTOREFRESH = False if not DEBUG else True
WHITENOISE_USE_FINDERS = False
WHITENOISE_MANIFEST_STRICT = False

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        # Use compressed manifest storage for cache busting
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# --- Supabase S3 Credentials (for media files) ---
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

# --- Cloudinary Configuration (Image CDN) ---
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '')

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

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

CSRF_TRUSTED_ORIGINS = ['https://blogsphere.up.railway.app']

# Google Analytics
GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', '')

# Contact Form Email
CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL', 'info@blogsphere.ng')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@blogsphere.ng')

# Email Backend (development - prints to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Site Configuration
SITE_DOMAIN = os.environ.get('SITE_DOMAIN', 'blogsphere.up.railway.app')
SITE_NAME = 'BlogSphere'

# Social Media
TWITTER_HANDLE = os.environ.get('TWITTER_HANDLE', '@BlogSphereNG')

# --- Security Settings (Production only) ---
if not DEBUG:
    # HTTPS/SSL
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


    # HSTS
    SECURE_HSTS_SECONDS = 31536000          # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Other security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# --- Logging Configuration ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# --- Cache Configuration (Optional Redis) ---
# Uncomment if you have Redis available on Railway
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': os.environ.get('REDIS_URL'),
#         'OPTIONS': {
#             'db': 1,
#             'parser_class': 'redis.connection.PythonParser',
#             'pool_class': 'redis.BlockingConnectionPool',
#         }
#     }
# }

# --- Session Configuration ---
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600                 # 2 weeks
SESSION_SAVE_EVERY_REQUEST = False

# --- File Upload Limits ---
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880        # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880        # 5MB

# Performance Summary
# -------------------
# ✅ GZip Compression enabled
# ✅ Static files compressed with WhiteNoise (manifest storage)
# ✅ Browser caching (1 year for static)
# ✅ Database connection pooling (10 min keep-alive)
# ✅ Template caching (production)
# ✅ Security headers & HTTPS (production)
# ✅ Cloudinary for image optimization
# ✅ Logging configured
# ✅ Session & upload limits optimized