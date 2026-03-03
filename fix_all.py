# fix_all.py
import os

print("🔄 Fixing all issues...")

# 1. Update views.py with complete version
views_content = '''# blog/views.py - COMPLETE VERSION WITH ALL FUNCTIONS
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Post, Category, Comment, NewsArticle
from django.core.paginator import Paginator

# ===== BASIC VIEWS =====

def home(request):
    """Homepage view"""
    featured_posts = Post.objects.filter(is_featured=True)[:3]
    latest_posts = Post.objects.all()[:8]

    context = {
        'featured_posts': featured_posts,
        'latest_posts': latest_posts,
    }
    return render(request, 'blog/home.html', context)

def post_detail(request, slug):
    """Individual post detail view"""
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
    """Category posts listing view"""
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
    """Search results view"""
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

    return render(request, 'blog/news_dashboard.html', context)

# ===== ENHANCED NEWS DASHBOARD VIEWS =====

def is_staff(user):
    """Check if user is staff"""
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def enhanced_news_dashboard(request):
    """Enhanced news dashboard view"""
    # Get statistics
    total_articles = NewsArticle.objects.count()
    today_articles = NewsArticle.objects.filter(
        imported_at__date=timezone.now().date()
    ).count()

    # Count auto-generated posts
    auto_posts = Post.objects.filter(title__startswith='[News]').count()
    to_process = NewsArticle.objects.filter(created_as_post=False).count()

    # Get recent articles
    recent_articles = NewsArticle.objects.order_by('-imported_at')[:20]

    # Get categories
    categories = Category.objects.all()

    # Mock scheduled jobs (for demo - you can implement real job tracking later)
    scheduled_jobs = [
        {
            'id': 1,
            'name': 'Hourly News Fetch',
            'schedule': 'Every hour',
            'last_run': timezone.now() - timezone.timedelta(minutes=30),
            'next_run': timezone.now() + timezone.timedelta(minutes=30),
            'is_active': True,
        },
        {
            'id': 2,
            'name': 'Daily Post Generation',
            'schedule': '9:00 AM daily',
            'last_run': timezone.now() - timezone.timedelta(hours=15),
            'next_run': timezone.now() + timezone.timedelta(hours=9),
            'is_active': True,
        },
    ]

    context = {
        'stats': {
            'total_articles': total_articles,
            'today_articles': today_articles,
            'auto_posts': auto_posts,
            'to_process': to_process,
        },
        'recent_articles': recent_articles,
        'categories': categories,
        'scheduled_jobs': scheduled_jobs,
    }

    return render(request, 'blog/enhanced-news-dashboard.html', context)

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def fetch_news_now(request):
    """AJAX endpoint to fetch news immediately"""
    if request.method == 'POST':
        try:
            # Get categories and sources from POST data
            categories = request.POST.getlist('categories', ['news', 'sport', 'entertainment'])
            sources = request.POST.getlist('sources', ['google', 'reddit'])

            # Import and use the enhanced news fetcher
            from blog.ai_service import EnhancedNewsFetcher
            fetcher = EnhancedNewsFetcher()
            articles = fetcher.fetch_multiple_sources(
                categories=categories,
                sources=sources,
                limit_per_source=3
            )

            # Save articles
            saved_count = 0
            for article in articles:
                if not NewsArticle.objects.filter(url=article['url']).exists():
                    NewsArticle.objects.create(
                        title=article['title'][:499],
                        content=article.get('content', '')[:5000],
                        summary=article.get('description', '')[:500],
                        url=article['url'],
                        source=article.get('source', 'Unknown'),
                        category=article.get('category', 'NEWS'),
                        image_url=article.get('image_url', ''),
                        published_at=timezone.now(),
                    )
                    saved_count += 1

            return JsonResponse({
                'success': True,
                'message': f'Fetched and saved {saved_count} new articles'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def generate_posts_now(request):
    """AJAX endpoint to generate posts immediately"""
    if request.method == 'POST':
        try:
            count = int(request.POST.get('count', 5))
            category_filter = request.POST.get('category', '')

            # Get articles to convert
            queryset = NewsArticle.objects.filter(created_as_post=False)
            if category_filter:
                queryset = queryset.filter(category=category_filter)

            articles = queryset.order_by('-published_at')[:count]

            from blog.ai_service import EnhancedNewsFetcher
            fetcher = EnhancedNewsFetcher()
            created_count = 0

            for article in articles:
                article_dict = {
                    'title': article.title,
                    'description': article.summary,
                    'content': article.content,
                    'url': article.url,
                    'source': article.source,
                    'category': article.category,
                    'published_at': article.published_at.isoformat() if article.published_at else None,
                }

                post = fetcher.generate_blog_post_from_article(article_dict)
                if post:
                    article.created_as_post = True
                    article.save()
                    created_count += 1

            return JsonResponse({
                'success': True,
                'message': f'Generated {created_count} blog posts'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
@user_passes_test(is_staff)
def dashboard_stats(request):
    """AJAX endpoint for dashboard statistics"""
    total_articles = NewsArticle.objects.count()
    today_articles = NewsArticle.objects.filter(
        imported_at__date=timezone.now().date()
    ).count()
    auto_posts = Post.objects.filter(title__startswith='[News]').count()
    to_process = NewsArticle.objects.filter(created_as_post=False).count()

    return JsonResponse({
        'total_articles': total_articles,
        'today_articles': today_articles,
        'auto_posts': auto_posts,
        'to_process': to_process,
    })

# ===== HELPER VIEWS =====

@login_required
@user_passes_test(is_staff)
def convert_to_post(request, article_id):
    """Convert a single news article to blog post"""
    try:
        article = NewsArticle.objects.get(id=article_id)

        from blog.ai_service import EnhancedNewsFetcher
        fetcher = EnhancedNewsFetcher()

        article_dict = {
            'title': article.title,
            'description': article.summary,
            'content': article.content,
            'url': article.url,
            'source': article.source,
            'category': article.category,
            'published_at': article.published_at.isoformat() if article.published_at else None,
        }

        post = fetcher.generate_blog_post_from_article(article_dict)
        if post:
            article.created_as_post = True
            article.save()
            return JsonResponse({
                'success': True,
                'message': f'Created post: {post.title}'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to create post'
            })

    except NewsArticle.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Article not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })'''

with open('blog/views.py', 'w') as f:
    f.write(views_content)
print("✅ Updated views.py")

# 2. Update urls.py
urls_content = '''from django.urls import path
from . import views

urlpatterns = [
    # Basic URLs
    path('', views.home, name='home'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('category/<slug:slug>/', views.category_posts, name='category_posts'),
    path('search/', views.search, name='search'),
    path('news-dashboard/', views.news_dashboard, name='news_dashboard'),

    # Enhanced news dashboard URLs
    path('enhanced-news-dashboard/', views.enhanced_news_dashboard, name='enhanced_news_dashboard'),
    path('api/fetch-news-now/', views.fetch_news_now, name='fetch_news_now'),
    path('api/generate-posts-now/', views.generate_posts_now, name='generate_posts_now'),
    path('api/dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
    path('api/convert-to-post/<int:article_id>/', views.convert_to_post, name='convert_to_post'),
]'''

with open('blog/urls.py', 'w') as f:
    f.write(urls_content)
print("✅ Updated urls.py")

# 3. Check admin.py for print statements
admin_file = 'blog/admin.py'
if os.path.exists(admin_file):
    with open(admin_file, 'r') as f:
        content = f.read()

    if 'print("✅ Admin panel ready!")' in content or 'print("👉 Visit:")' in content:
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            if not line.strip().startswith('print('):
                cleaned_lines.append(line)

        with open(admin_file, 'w') as f:
            f.write('\n'.join(cleaned_lines))
        print("✅ Cleaned admin.py print statements")

print("\n🎉 All fixes applied!")
print("\nNow run:")
print("1. python manage.py makemigrations")
print("2. python manage.py migrate")
print("3. python manage.py runserver")