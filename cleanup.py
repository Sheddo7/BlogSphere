# cleanup.py
import os

# 1. Fix admin.py
admin_file = 'blog/admin.py'
if os.path.exists(admin_file):
    with open(admin_file, 'r') as f:
        content = f.read()

    # Remove print statements at the end
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        if not ('print("✅ Admin panel ready!")' in line or
                'print("👉 Visit:' in line):
            cleaned_lines.append(line)

    with open(admin_file, 'w') as f:
        f.write('\n'.join(cleaned_lines))
    print("✅ Cleaned admin.py")

# 2. Create/update views.py with correct functions
views_content = '''from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Post, Category, Comment, NewsArticle
from django.core.paginator import Paginator

def home(request):
    featured_posts = Post.objects.filter(is_featured=True)[:3]
    latest_posts = Post.objects.all()[:8]

    context = {
        'featured_posts': featured_posts,
        'latest_posts': latest_posts,
    }
    return render(request, 'blog/home.html', context)

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    post.views += 1
    post.save()

    # Get comments for this post
    comments = Comment.objects.filter(post=post, is_approved=True)

    related_posts = Post.objects.filter(category=post.category).exclude(id=post.id)[:3]

    context = {
        'post': post,
        'related_posts': related_posts,
        'comments': comments,
    }
    return render(request, 'blog/post_detail.html', context)

def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts_list = Post.objects.filter(category=category)
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'category': category,
    }
    return render(request, 'blog/category.html', context)

def search(request):
    query = request.GET.get('q', '')
    if query:
        results = Post.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query)
        ).distinct()
    else:
        results = Post.objects.none()

    context = {
        'results': results,
        'query': query,
    }
    return render(request, 'blog/search.html', context)

def news_dashboard(request):
    """Simple dashboard to view fetched news"""
    if not request.user.is_authenticated:
        return redirect('admin:login')

    # Get stats
    total_articles = NewsArticle.objects.count()
    recent_articles = NewsArticle.objects.order_by('-imported_at')[:10]

    # Group by category
    from django.db.models import Count
    category_stats = NewsArticle.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')

    context = {
        'total_articles': total_articles,
        'recent_articles': recent_articles,
        'category_stats': category_stats,
    }

    return render(request, 'blog/news_dashboard.html', context)'''

with open('blog/views.py', 'w') as f:
    f.write(views_content)
print("✅ Updated views.py with basic functions")

# 3. Update urls.py
urls_content = '''from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('category/<slug:slug>/', views.category_posts, name='category_posts'),
    path('search/', views.search, name='search'),
    path('news-dashboard/', views.news_dashboard, name='news_dashboard'),
]'''

with open('blog/urls.py', 'w') as f:
    f.write(urls_content)
print("✅ Updated urls.py")

print("\n🎉 Cleanup complete! Now run:")
print("1. python manage.py makemigrations")
print("2. python manage.py migrate")
print("3. python manage.py runserver")