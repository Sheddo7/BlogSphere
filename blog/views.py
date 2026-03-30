# blog/views.py - COMPLETE UPDATED VERSION WITH ALL FUNCTIONS (COMMENTS REMOVED)
import os

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count, F
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from .models import Post, NewsArticle
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from blog.ai_service import OpenRouterService
import logging
from django.http import HttpResponseServerError
from django.shortcuts import render
from .models import Category
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
import bleach



# ===== BASIC VIEWS =====

def format_content(text):
    """Convert plain text content into proper HTML paragraphs."""
    if not text:
        return ''
    # If content already has HTML tags leave it alone
    if '<p>' in text or '<div>' in text or '<h2>' in text:
        return text
    # Split on double newlines or single newlines
    import re
    paragraphs = re.split(r'\n\n+|\n', text)
    formatted = ''
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Detect headings — lines that are short and don't end with punctuation
        if len(para) < 80 and not para.endswith(('.', ',', '?', '!')):
            formatted += f'<h3>{para}</h3>\n'
        else:
            formatted += f'<p>{para}</p>\n'
    return formatted


def home(request):
    featured_posts = Post.objects.filter(is_featured=True).select_related('category', 'author')[:3]
    latest_posts = Post.objects.all().select_related('category', 'author')[:8]
    context = {
        'featured_posts': featured_posts,
        'latest_posts': latest_posts,
    }
    return render(request, 'blog/home.html', context)


def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.select_related('category', 'author').prefetch_related('tags'),
        slug=slug
    )
    Post.objects.filter(pk=post.pk).update(views=F('views') + 1)

    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'a', 'img', 'figure', 'figcaption',
        'code', 'pre', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
    ]
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title', 'target', 'rel'],
        'img': ['src', 'alt', 'width', 'height', 'loading'],
        '*': ['class'],
    }

    clean_content = bleach.clean(
        post.content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

    related_posts = Post.objects.filter(
        category=post.category
    ).exclude(id=post.id).select_related('category')[:3]

    context = {
        'post': post,
        'clean_content': clean_content,
        'related_posts': related_posts,
    }
    return render(request, 'blog/post_detail.html', context)


logger = logging.getLogger(__name__)


def category_posts(request, slug):
    try:
        category = get_object_or_404(Category, slug=slug)
        posts_list = Post.objects.filter(
            category=category
        ).select_related('category', 'author')
        paginator = Paginator(posts_list, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
        categories = Category.objects.annotate(
            post_count=Count('posts')
        ).order_by('-post_count')
        context = {
            'page_obj': page_obj,
            'category': category,
            'categories': categories,
        }
        return render(request, 'blog/category.html', context)
    except Exception as e:
        logger.error(f"Error in category_posts for slug '{slug}': {e}", exc_info=True)
        return HttpResponseServerError("An internal error occurred.")


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

    total_articles = NewsArticle.objects.count()
    recent_articles = NewsArticle.objects.order_by('-imported_at')[:10]
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
    """AJAX endpoint to fetch news immediately"""
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
            return JsonResponse({'success': True, 'message': f'Generated {created_count} blog posts'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
@user_passes_test(is_staff)
def dashboard_stats(request):
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
    """Post article with AI content generation – accepts pre-generated content."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            article = data.get('article')
            if not article:
                return JsonResponse({'success': False, 'message': 'No article data provided'})

            category_name = article.get('category', 'NEWS')
            from django.utils.text import slugify
            from django.contrib.auth.models import User
            from blog.models import Category, Post

            category_obj, created = Category.objects.get_or_create(name=category_name)

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

            provided_content = data.get('content')
            provided_summary = data.get('summary')
            provided_word_count = data.get('word_count')

            if provided_content:
                article_content = provided_content
                article_description = provided_summary or article.get('description', '')[:200]
                word_count = provided_word_count or len(article_content.split())
                ai_processed = True
            else:
                from blog.ai_service import EnhancedNewsFetcher
                processed_article = EnhancedNewsFetcher.process_article_with_ai(article)
                if processed_article is None:
                    return JsonResponse({'success': False, 'message': 'Could not generate content (scraping failed)'})
                article_content = processed_article.get('content', '')
                article_description = processed_article.get('description', '')[:200]
                word_count = processed_article.get('word_count', 0)
                ai_processed = processed_article.get('ai_processed', False)

            post = Post.objects.create(
                title=article['title'][:200],
                slug=slug,
                content=format_content(article_content),
                excerpt=article_description,
                author=author,
                category=category_obj,
                image_url=article.get('image_url', ''),
                published_date=timezone.now(),
                is_featured=data.get('is_featured', False)
            )

            tags = data.get('tags', ['news'])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',')]
            for tag in tags:
                post.tags.add(tag.strip())

            # Save as NewsArticle if requested
            if data.get('save_article', True):
                from blog.models import NewsArticle
                if not NewsArticle.objects.filter(url=article.get('url', '')).exists():
                    NewsArticle.objects.create(
                        title=article['title'][:499],
                        content=article_content[:5000],
                        summary=article_description[:500],
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
                'post_slug': post.slug,
                'word_count': word_count,
                'ai_processed': ai_processed,
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
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

            for article in articles:
                category_name = article.get('category', 'NEWS')
                from django.utils.text import slugify
                from django.contrib.auth.models import User

                category_obj, created = Category.objects.get_or_create(name=category_name)

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

                post = Post.objects.create(
                    title=article['title'][:200],
                    slug=slug,
                    content=article.get('content', article.get('description', ''))[:5000],
                    excerpt=article.get('description', '')[:200],
                    author=author,
                    category=category_obj,
                    image_url=article.get('image_url', ''),
                    published_date=timezone.now(),
                )

                tags = data.get('tags', ['news'])
                if isinstance(tags, str):
                    tags = [tag.strip() for tag in tags.split(',')]
                for tag in tags:
                    post.tags.add(tag.strip())

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


@csrf_exempt
@login_required
@user_passes_test(is_staff)
def openrouter_chat(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        temperature = float(data.get('temperature', 0.7))
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)

        service = OpenRouterService()
        result = service.generate_response(message, temperature=temperature)

        if result['success']:
            return JsonResponse({
                'success': True,
                'content': result['content'],
                'word_count': result['word_count']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }, status=500)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@user_passes_test(is_staff)
def preview_article(request):
    """Generate AI content for preview without saving."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            article = data.get('article')
            if not article:
                return JsonResponse({'success': False, 'message': 'No article data provided'})

            from blog.ai_service import EnhancedNewsFetcher
            processed = EnhancedNewsFetcher.process_article_with_ai(article)
            if processed is None:
                return JsonResponse({'success': False, 'message': 'Could not generate preview (scraping failed)'})

            content = processed.get('content', '')
            # Limit content to 50,000 characters to avoid response size issues
            if len(content) > 50000:
                content = content[:50000] + "\n\n...[content truncated due to length]"
            summary = processed.get('description', '')[:200]

            return JsonResponse({
                'success': True,
                'content': content,
                'summary': summary,
                'word_count': processed.get('word_count', 0)
            })
        except Exception as e:
            import traceback
            traceback.print_exc()  # Log the full error to Railway console
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def custom_404(request, exception):
    """Custom 404 page with categories and search."""
    # Get categories with post counts, ordered by popularity
    categories = Category.objects.annotate(post_count=Count('posts')).order_by('-post_count')[:6]
    return render(request, '404.html', {'categories': categories}, status=404)


@login_required
@user_passes_test(is_staff)
def combined_dashboard(request):
    """Single dashboard with all stats, recent articles, posts, fetch form, and scheduled jobs."""
    # Stats
    total_articles = NewsArticle.objects.count()
    today_articles = NewsArticle.objects.filter(
        imported_at__date=timezone.now().date()
    ).count()
    auto_posts = Post.objects.filter(title__startswith='[News]').count()
    to_process = NewsArticle.objects.filter(created_as_post=False).count()

    # Recent articles
    recent_articles = NewsArticle.objects.order_by('-imported_at')[:20]

    # Recent posts
    recent_posts = Post.objects.order_by('-published_date')[:10]

    # Categories
    categories = Category.objects.all()

    # Category stats
    category_stats = NewsArticle.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')

    # Mock scheduled jobs (you can replace with real job data)
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
        'category_stats': category_stats,
        'scheduled_jobs': scheduled_jobs,
    }
    return render(request, 'blog/combined_dashboard.html', context)


# Backward compatibility alias
auto_fetch_news = fetch_news_now


# ==============================================================================
# DRAFT WORKFLOW VIEWS
# ==============================================================================

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def save_as_draft(request):
    """Process article with AI and save as DRAFT (not published yet)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            article = data.get('article')

            if not article:
                return JsonResponse({'success': False, 'message': 'No article data provided'})

            print(f"\n🤖 PROCESSING ARTICLE AS DRAFT")
            print(f"Title: {article['title'][:60]}")

            # Process with AI
            from blog.ai_service import EnhancedNewsFetcher
            processed_article = EnhancedNewsFetcher.process_article_with_ai(article)

            # Save as NewsArticle with status='draft'
            news_article, created = NewsArticle.objects.update_or_create(
                url=article.get('url', ''),
                defaults={
                    'title': article['title'][:499],
                    'content': processed_article.get('content', article.get('description', '')),
                    'summary': processed_article.get('description', article.get('description', ''))[:500],
                    'source': article.get('source', 'Unknown'),
                    'category': article.get('category', 'NEWS'),
                    'image_url': article.get('image_url', ''),
                    'published_at': timezone.now(),
                    'status': 'draft',
                    'word_count': processed_article.get('word_count', 0),
                    'ai_processed': processed_article.get('ai_processed', False),
                    'tags': 'news',
                }
            )

            print(f"✅ Saved as draft: {news_article.id}")

            return JsonResponse({
                'success': True,
                'message': 'Article saved as draft',
                'draft_id': news_article.id,
                'word_count': news_article.word_count,
                'ai_processed': news_article.ai_processed,
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required
@user_passes_test(is_staff)
def get_drafts(request):
    """Get all draft articles"""
    try:
        drafts = NewsArticle.objects.filter(status='draft').order_by('-imported_at')[:50]

        drafts_data = [{
            'id': draft.id,
            'title': draft.title,
            'summary': draft.summary,
            'content': draft.content,
            'source': draft.source,
            'category': draft.category,
            'image_url': draft.image_url,
            'word_count': draft.word_count,
            'ai_processed': draft.ai_processed,
            'tags': draft.tags,
            'is_featured': draft.is_featured,
            'imported_at': draft.imported_at.strftime('%Y-%m-%d %H:%M'),
        } for draft in drafts]

        return JsonResponse({'success': True, 'drafts': drafts_data, 'count': len(drafts_data)})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@csrf_exempt
@login_required
@user_passes_test(is_staff)
def edit_draft(request, draft_id):
    """Edit a draft article"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            draft = NewsArticle.objects.get(id=draft_id, status='draft')

            draft.title = data.get('title', draft.title)
            draft.content = data.get('content', draft.content)
            draft.summary = data.get('summary', draft.summary)
            draft.category = data.get('category', draft.category)
            draft.tags = data.get('tags', draft.tags)
            draft.is_featured = data.get('is_featured', draft.is_featured)
            draft.image_url = data.get('image_url', draft.image_url)
            draft.word_count = len(draft.content.split())
            draft.save()

            return JsonResponse(
                {'success': True, 'message': 'Draft updated successfully', 'word_count': draft.word_count})

        except NewsArticle.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Draft not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required
@user_passes_test(is_staff)
def delete_draft(request, draft_id):
    """Delete a draft article"""
    if request.method == 'POST':
        try:
            draft = NewsArticle.objects.get(id=draft_id, status='draft')
            title = draft.title
            draft.delete()
            return JsonResponse({'success': True, 'message': f'Draft "{title}" deleted successfully'})

        except NewsArticle.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Draft not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required
@user_passes_test(is_staff)
def publish_draft(request, draft_id):
    """Publish a draft to the blog as a Post"""
    if request.method == 'POST':
        try:
            from django.contrib.auth.models import User
            from django.utils.text import slugify

            draft = NewsArticle.objects.get(id=draft_id, status='draft')

            category_obj, created = Category.objects.get_or_create(
                name=draft.category if draft.category else 'NEWS'
            )

            try:
                author = User.objects.get(username='admin')
            except User.DoesNotExist:
                author = User.objects.first()

            base_slug = slugify(draft.title[:50])
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            post = Post.objects.create(
                title=draft.title[:500],
                slug=slug,
                content=format_content(draft.content),
                excerpt=draft.summary[:500] if draft.summary else draft.title[:500],
                author=author,
                category=category_obj,
                image_url=draft.image_url if draft.image_url else '',
                published_date=timezone.now(),
                is_featured=draft.is_featured
            )

            tags = [tag.strip() for tag in draft.tags.split(',') if tag.strip()]
            for tag in tags:
                post.tags.add(tag)



            draft.status = 'published'
            draft.created_as_post = True
            draft.save()

            return JsonResponse({
                'success': True,
                'message': f'Published: {post.title}',
                'post_slug': post.slug,
                'post_id': post.id
            })

        except NewsArticle.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Draft not found'})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required
@user_passes_test(is_staff)
def update_draft_image(request, draft_id):
    """Update draft image URL"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            draft = NewsArticle.objects.get(id=draft_id, status='draft')
            draft.image_url = data.get('image_url', '')
            draft.save()
            return JsonResponse({'success': True, 'message': 'Image updated successfully'})

        except NewsArticle.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Draft not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request'})



def robots_txt(request):
    """Serve robots.txt with custom admin URL"""
    context = {
        'ADMIN_URL': settings.ADMIN_URL
    }
    return render(request, 'robots.txt', context, content_type='text/plain')


# Legal Pages Views
def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'blog/privacy_policy.html')


def about(request):
    """About Us page"""
    return render(request, 'blog/about.html')


def terms_of_service(request):
    """Terms of Service page"""
    return render(request, 'blog/terms.html')


def contact(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '')
            email = request.POST.get('email', '')
            subject_type = request.POST.get('subject', '')
            message = request.POST.get('message', '')

            if not all([name, email, message]):
                return JsonResponse({
                    'success': False,
                    'message': 'Please fill in all required fields.'
                })

            import resend
            resend.api_key = os.environ.get('RESEND_API_KEY', '')

            params = {
                "from": "BlogSphere <noreply@blogsphere.ng>",
                "to": [settings.CONTACT_EMAIL],
                "reply_to": email,
                "subject": f"BlogSphere Contact: {subject_type}",
                "text": f"""
New contact form submission

Name: {name}
Email: {email}
Subject: {subject_type}

Message:
{message}
                """
            }

            resend.Emails.send(params)

            return JsonResponse({
                'success': True,
                'message': 'Thank you for your message! We will get back to you within 24-48 hours.'
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

    return render(request, 'blog/contact.html')


def tag_posts(request, tag):
    from taggit.models import Tag
    from django.shortcuts import get_object_or_404

    tag_obj = get_object_or_404(Tag, slug=tag)
    posts_list = Post.objects.filter(
        tags__name__in=[tag_obj.name]
    ).select_related('category', 'author').distinct().order_by('-published_date')

    paginator = Paginator(posts_list, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'tag': tag_obj,
        'page_obj': page_obj,
    }
    return render(request, 'blog/tag_posts.html', context)