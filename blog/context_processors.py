# blog/context_processors.py
from .models import Category, Post

def categories_processor(request):
    categories = Category.objects.all()
    return {'categories': categories}

def latest_posts_processor(request):
    latest_posts = Post.objects.all()[:5]
    return {'latest_posts': latest_posts}