# blog/views.py - COMPLETE UPDATED VERSION WITH GEMINI INTEGRATION
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json

from .models import Post, Category, Comment, NewsArticle
from django.core.paginator import Paginator

# ===== BASIC VIEWS =====
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
    if not request.user.is_authenticated:
        return redirect('admin:login')
    total_articles = NewsArticle.objects.count()
    recent_articles = NewsArticle.objects.order_by('-imported_at')[:10]
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
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def enhanced_news_dashboard(request):
    total_articles = NewsArticle.objects.count()
    today_articles = NewsArticle.objects.filter(
        imported_at__date=timezone.now().date()
    ).count()
    auto_posts = Post.objects.filter(title__startswith='[News]').count()
    to_process = NewsArticle.objects.filter(created_as_post=False).count()
    recent_articles = NewsArticle.objects.order_by('-imported_at')[:20]
    recent_posts = Post.objects.order_by('-published_date')[:10]
    categories = Category.objects.all()
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
        'recent_posts': recent_posts,
        'categories': categories,
        'scheduled_jobs': scheduled_jobs,
    }
    return render(request, 'blog/enhanced-news-dashboard.html', context)

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def fetch_news_now(request):
    if request.method == 'POST':
        try:
            categories = request.POST.getlist('categories', ['news', 'sport', 'entertainment'])
            sources = request.POST.getlist('sources', ['google', 'reddit'])
            limit_per_source = int(request.POST.get('limit_per_source', 3))
            from blog.ai_service import EnhancedNewsFetcher
            fetcher = EnhancedNewsFetcher()
            articles = fetcher.fetch_multiple_sources(
                categories=categories,
                sources=sources,
                limit_per_source=limit_per_source
            )
            saved_count = 0
            auto_save = request.POST.get('auto_save') == 'true'
            if auto_save:
                for article in articles:
                    if not NewsArticle.objects.filter(url=article['url']).exists():
                        NewsArticle.objects.create(
                            title=article['title'][:499],
                            content=article.get('content', '')[:15000],  # increased
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
                'message': f'Fetched {len(articles)} articles' + (f' and saved {saved_count}' if auto_save else ''),
                'articles': articles,
                'saved_count': saved_count
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def generate_posts_now(request):
    if request.method == 'POST':
        try:
            count = int(request.POST.get('count', 5))
            category_filter = request.POST.get('category', '')
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
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
@user_passes_test(is_staff)
def dashboard_stats(request):
    total_articles = NewsArticle.objects.count()
    today_articles = NewsArticle.objects.filter(imported_at__date=timezone.now().date()).count()
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
            return JsonResponse({'success': True, 'message': f'Created post: {post.title}'})
        else:
            return JsonResponse({'success': False, 'message': 'Failed to create post'})
    except NewsArticle.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Article not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

# ===== NEW API ENDPOINTS =====
@csrf_exempt
@login_required
@user_passes_test(is_staff)
def post_article(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            article = data.get('article')
            if not article:
                return JsonResponse({'success': False, 'message': 'No article data provided'})
            category_name = article.get('category', 'NEWS')
            from django.utils.text import slugify
            from django.contrib.auth.models import User
            category_obj, _ = Category.objects.get_or_create(name=category_name)
            try:
                author = User.objects.get(username='admin')
            except User.DoesNotExist:
                author = User.objects.first()
            base_slug = slugify(article['title'][:50])
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            # Create blog post – the content will be rewritten by Gemini inside generate_blog_post_from_article
            # But we are not calling that here; we just save the article data as a Post.
            # However, to use Gemini, we should call generate_blog_post_from_article instead of manual creation.
            # Let's change this: use the AI method.
            from blog.ai_service import EnhancedNewsFetcher
            post = EnhancedNewsFetcher.generate_blog_post_from_article(article, use_ai=True)
            if not post:
                return JsonResponse({'success': False, 'message': 'Failed to create post'})
            # Also save as NewsArticle if requested
            if data.get('save_article', True):
                if not NewsArticle.objects.filter(url=article.get('url', '')).exists():
                    NewsArticle.objects.create(
                        title=article['title'][:499],
                        content=article.get('content', '')[:15000],
                        summary=article.get('description', '')[:500],
                        url=article.get('url', ''),
                        source=article.get('source', 'Unknown'),
                        category=category_name,
                        image_url=article.get('image_url', ''),
                        published_at=timezone.now(),
                        created_as_post=True
                    )
            return JsonResponse({
                'success': True,
                'message': 'Article posted successfully',
                'post_title': post.title,
                'post_slug': post.slug
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def post_multiple_articles(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            articles = data.get('articles', [])
            posted_count = 0
            post_titles = []
            from blog.ai_service import EnhancedNewsFetcher
            for article in articles:
                post = EnhancedNewsFetcher.generate_blog_post_from_article(article, use_ai=True)
                if post:
                    posted_count += 1
                    post_titles.append(post.title)
            return JsonResponse({
                'success': True,
                'message': f'Posted {posted_count} articles',
                'posted_count': posted_count,
                'post_titles': post_titles
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def get_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        return JsonResponse({
            'success': True,
            'post': {
                'id': post.id,
                'title': post.title,
                'category': post.category.name if post.category else 'Uncategorized',
                'featured_image': post.featured_image.url if post.featured_image else '',
                'slug': post.slug,
                'content': post.content[:500] if post.content else '',
                'published_date': post.published_date.strftime('%Y-%m-%d') if post.published_date else '',
            }
        })
    except Post.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Post not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def update_post_image(request):
    if request.method == 'POST':
        try:
            post_id = request.POST.get('post_id')
            use_default = request.POST.get('use_default') == 'true'
            post = Post.objects.get(id=post_id)
            if use_default:
                post.featured_image = 'blog_images/default.jpg'
                post.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Default image set successfully',
                    'image_url': '/media/blog_images/default.jpg'
                })
            if 'image' in request.FILES:
                image_file = request.FILES['image']
                if image_file.size > 5 * 1024 * 1024:
                    return JsonResponse({'success': False, 'message': 'File size too large (max 5MB)'})
                file_name = default_storage.save(
                    f'blog_images/{post.slug}_{image_file.name}',
                    ContentFile(image_file.read())
                )
                post.featured_image = file_name
                post.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Image uploaded successfully',
                    'image_url': f'/media/{file_name}'
                })
            image_url = request.POST.get('image_url')
            if image_url:
                post.featured_image = image_url
                post.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Image URL saved successfully',
                    'image_url': image_url
                })
            return JsonResponse({'success': False, 'message': 'No image provided'})
        except Post.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Post not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def remove_post_image(request, post_id):
    if request.method == 'POST':
        try:
            post = Post.objects.get(id=post_id)
            post.featured_image = None
            post.save()
            return JsonResponse({'success': True, 'message': 'Image removed successfully'})
        except Post.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Post not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
@user_passes_test(is_staff)
def delete_news_article(request, article_id):
    if request.method == 'DELETE':
        try:
            article = NewsArticle.objects.get(id=article_id)
            article.delete()
            return JsonResponse({'success': True, 'message': 'Article deleted successfully'})
        except NewsArticle.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Article not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_staff)
def delete_post(request, post_id):
    if request.method == 'DELETE':
        try:
            post = Post.objects.get(id=post_id)
            post.delete()
            return JsonResponse({'success': True, 'message': 'Post deleted successfully'})
        except Post.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Post not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

# ===== NEW COLLATION ENDPOINT =====
@csrf_exempt
@login_required
@user_passes_test(is_staff)
def collate_articles(request):
    """Collate multiple selected articles into one AI-generated post"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            article_indices = data.get('indices', [])
            fetched_articles = data.get('articles', [])
            if not article_indices or not fetched_articles:
                return JsonResponse({'success': False, 'message': 'No articles selected'})
            articles_to_collate = [fetched_articles[i] for i in article_indices if i < len(fetched_articles)]
            from blog.ai_service import EnhancedNewsFetcher
            collated = EnhancedNewsFetcher.collate_articles(articles_to_collate)
            if not collated:
                return JsonResponse({'success': False, 'message': 'Could not collate articles'})
            post = EnhancedNewsFetcher.generate_blog_post_from_article(collated, use_ai=True)
            if post:
                return JsonResponse({
                    'success': True,
                    'message': f'Collated post created: {post.title}',
                    'post_id': post.id,
                    'post_title': post.title
                })
            else:
                return JsonResponse({'success': False, 'message': 'Failed to create post'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required
@user_passes_test(is_staff)
def preview_rewrite(request):
    """Generate a rewritten version of an article (Gemini) and return it without saving."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            article = data.get('article')
            if not article:
                return JsonResponse({'success': False, 'message': 'No article data'})

            from blog.ai_service import EnhancedNewsFetcher

            # Fetch full content if needed
            content_text = article.get('content', '')
            if len(content_text) < 500 and article.get('url'):
                content_text = EnhancedNewsFetcher.extract_content_from_url(article['url']) or ''

            if not content_text or len(content_text) < 200:
                return JsonResponse({'success': False, 'message': 'Not enough content to rewrite.'})

            # Run Gemini
            rewritten = EnhancedNewsFetcher.rewrite_with_gemini(content_text, target_words=500)
            word_count = len(rewritten.split())

            return JsonResponse({
                'success': True,
                'rewritten': rewritten,
                'word_count': word_count,
                'title': article.get('title', ''),
                'source': article.get('source', ''),
                'category': article.get('category', 'NEWS'),
                'url': article.get('url', ''),
                'image_url': article.get('image_url', ''),
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def save_rewritten(request):
    """Save a previously rewritten article as a blog post."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            article = data.get('article')  # original article data
            rewritten = data.get('rewritten')
            if not article or not rewritten:
                return JsonResponse({'success': False, 'message': 'Missing data'})

            from django.utils.text import slugify
            from django.contrib.auth.models import User
            from blog.models import Category, Post
            from django.utils import timezone

            category_name = article.get('category', 'NEWS')
            category_obj, _ = Category.objects.get_or_create(name=category_name)

            try:
                author = User.objects.get(username='admin')
            except User.DoesNotExist:
                author = User.objects.first()

            base_slug = slugify(article['title'][:50])
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Build the post content with the rewritten article
            enhanced_content = f"""
<h1>{article['title']}</h1>
<div class="alert alert-info">
    <strong>Source:</strong> {article.get('source', 'Unknown')}<br>
    <strong>Original URL:</strong> <a href="{article['url']}" target="_blank" rel="noopener">{article['url'][:100]}...</a>
</div>
<hr>
<h3>Article (AI‑generated summary)</h3>
<div class='article-content'>{rewritten}</div>
<hr>
<div class="alert alert-secondary">
    <em>This article was automatically generated from {article.get('source', 'a news source')}. 
    <a href="{article.get('url', '#')}" target="_blank" class="btn btn-sm btn-outline-primary">
        Read original article
    </a></em>
</div>
"""

            post = Post.objects.create(
                title=f"[News] {article['title'][:100]}",
                slug=slug,
                content=enhanced_content,
                excerpt=article.get('description', '')[:300] or article.get('title', '')[:200],
                author=author,
                category=category_obj,
                featured_image=article.get('image_url', ''),
                published_date=timezone.now(),
            )
            post.tags.add('news', article.get('category', 'general').lower())

            # Optionally save as NewsArticle
            if data.get('save_article', True):
                if not NewsArticle.objects.filter(url=article.get('url', '')).exists():
                    NewsArticle.objects.create(
                        title=article['title'][:499],
                        content=rewritten[:15000],
                        summary=article.get('description', '')[:500],
                        url=article.get('url', ''),
                        source=article.get('source', 'Unknown'),
                        category=category_name,
                        image_url=article.get('image_url', ''),
                        published_at=timezone.now(),
                        created_as_post=True
                    )

            return JsonResponse({
                'success': True,
                'message': 'Article saved successfully',
                'post_title': post.title,
                'post_slug': post.slug
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

# Backward compatibility alias
auto_fetch_news = fetch_news_now