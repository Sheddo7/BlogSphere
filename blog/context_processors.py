# blog/context_processors.py
from django.core.cache import cache  # <-- added
from .models import Category, Post
from django.conf import settings

def categories_processor(request):
    """
    Returns all categories, cached for 1 hour.
    """
    categories = cache.get('all_categories')
    if not categories:
        categories = list(Category.objects.all())
        cache.set('all_categories', categories, 3600)  # 1 hour
    return {'categories': categories}

def latest_posts_processor(request):
    """
    Returns the 5 most recent posts, cached for 5 minutes.
    """
    latest_posts = cache.get('latest_posts')
    if not latest_posts:
        latest_posts = list(Post.objects.order_by('-published_date')[:5])
        cache.set('latest_posts', latest_posts, 300)  # 5 minutes
    return {'latest_posts': latest_posts}

def seo_defaults(request):
    """
    Provides global SEO variables for all templates.
    These are request-dependent and not cached.
    """
    site_url = request.build_absolute_uri('/')[:-1]
    default_social = settings.STATIC_URL + 'img/social-default.jpg'
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'BlogSphere'),
        'site_url': site_url,
        'twitter_handle': getattr(settings, 'TWITTER_HANDLE', '@BlogSphereNG'),
        'default_social_image': request.build_absolute_uri(default_social),
    }