# blog/context_processors.py
from .models import Category, Post
from django.conf import settings

def categories_processor(request):
    categories = Category.objects.all()
    return {'categories': categories}

def latest_posts_processor(request):
    latest_posts = Post.objects.all()[:5]
    return {'latest_posts': latest_posts}



def seo_defaults(request):
    site_url = request.build_absolute_uri('/')[:-1]
    default_social = settings.STATIC_URL + 'img/social-default.jpg'
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'BlogSphere'),
        'site_url': site_url,
        'social_twitter_url': getattr(settings, 'TWITTER_URL', '#'),
        'social_facebook_url': getattr(settings, 'FACEBOOK_URL', '#'),
        'default_social_image': request.build_absolute_uri(default_social),
        'google_analytics_id': getattr(settings, 'GOOGLE_ANALYTICS_ID', ''),
    }