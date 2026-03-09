# blog/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
from django.core.files import File
import tempfile

from .models import Post, Category, Comment, NewsArticle
from django.core.paginator import Paginator


# ── Helper ──────────────────────────────────────────────────────
def is_staff(user):
    return user.is_staff


# ── Public views ────────────────────────────────────────────────

def home(request):
    featured_posts = list(Post.objects.filter(is_featured=True)[:6])
    # If fewer than 2 featured posts, top up from latest
    if len(featured_posts) < 2:
        featured_ids = [p.id for p in featured_posts]
        extras = Post.objects.exclude(id__in=featured_ids)[:6 - len(featured_posts)]
        featured_posts = list(featured_posts) + list(extras)
    latest_posts = Post.objects.all()[:12]
    categories = Category.objects.all()
    return render(request, 'blog/home.html', {
        'featured_posts': featured_posts,
        'latest_posts': latest_posts,
        'categories': categories,
    })


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    post.views += 1
    post.save()
    comments = Comment.objects.filter(post=post, is_approved=True)
    related_posts = Post.objects.filter(category=post.category).exclude(id=post.id)[:3]
    latest_posts = Post.objects.all()[:6]
    categories = Category.objects.all()
    return render(request, 'blog/post_detail.html', {
        'post': post,
        'related_posts': related_posts,
        'comments': comments,
        'latest_posts': latest_posts,
        'categories': categories,
    })


def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)
    categories = Category.objects.all()
    posts_list = Post.objects.filter(category=category)
    paginator = Paginator(posts_list, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog/category.html', {
        'page_obj': page_obj,
        'category': category,
        'categories': categories,
    })


def search(request):
    query = request.GET.get('q', '')
    categories = Category.objects.all()
    results = Post.objects.filter(
        Q(title__icontains=query) |
        Q(content__icontains=query) |
        Q(excerpt__icontains=query)
    ).distinct() if query else Post.objects.none()
    return render(request, 'blog/search.html', {
        'results': results,
        'query': query,
        'categories': categories,
    })


# ── Admin-only dashboards ────────────────────────────────────────

@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
def news_dashboard(request):
    total_articles = NewsArticle.objects.count()
    recent_articles = NewsArticle.objects.order_by('-imported_at')[:10]
    category_stats = NewsArticle.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    return render(request, 'blog/news_dashboard.html', {
        'total_articles': total_articles,
        'recent_articles': recent_articles,
        'category_stats': category_stats,
    })


@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
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
            'name': 'Auto News Fetch',
            'schedule': 'Every 2 hours',
            'last_run': timezone.now() - timezone.timedelta(hours=1),
            'next_run': timezone.now() + timezone.timedelta(hours=1),
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

    # ---- NEW: Category counts (including zero) ----
    all_categories = Category.objects.all()
    category_counts = []
    for cat in all_categories:
        # Count posts in this category - adjust filter if you have a status field
        count = Post.objects.filter(category=cat).count()
        category_counts.append({'name': cat.name, 'count': count})

    # ---- NEW: Three most recent posts for "Latest Stories" ----
    latest_stories = Post.objects.order_by('-published_date')[:3]

    return render(request, 'blog/enhanced-news-dashboard.html', {
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
        'category_counts': category_counts,
        'latest_stories': latest_stories,
    })


# ── News fetching APIs (admin only) ─────────────────────────────

def _do_fetch_and_save(categories=None, sources=None, limit=5):
    """
    Core fetch logic — shared by auto_fetch_news (manual button)
    and the scheduler job.
    Returns (total_fetched, saved_count).
    """
    if categories is None:
        categories = ['news', 'sport', 'entertainment', 'economy', 'politics', 'technology']
    if sources is None:
        sources = ['google', 'google_nigeria', 'punch', 'vanguard', 'channels']

    from blog.ai_service import EnhancedNewsFetcher
    fetcher = EnhancedNewsFetcher()
    articles = fetcher.fetch_multiple_sources(
        categories=categories,
        sources=sources,
        limit_per_source=limit
    )

    saved_count = 0
    for article in articles:
        url = article.get('url', '')
        if url and not NewsArticle.objects.filter(url=url).exists():
            NewsArticle.objects.create(
                title=article.get('title', 'Untitled')[:499],
                content=article.get('content', '')[:5000],
                summary=article.get('description', '')[:500],
                url=url,
                source=article.get('source', 'Unknown'),
                category=article.get('category', 'NEWS'),
                image_url=article.get('image_url', ''),
                published_at=timezone.now(),
            )
            saved_count += 1

    return len(articles), saved_count


@csrf_exempt
@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
def auto_fetch_news(request):
    """
    Manual trigger from dashboard button.
    Also called internally by the scheduler every 2 hours.
    """
    if request.method == 'POST':
        try:
            try:
                data = json.loads(request.body)
            except Exception:
                data = {}

            total, saved = _do_fetch_and_save(
                categories=data.get('categories'),
                sources=data.get('sources'),
                limit=int(data.get('limit_per_source', 5)),
            )
            return JsonResponse({
                'success': True,
                'message': f'Fetched {total} articles, {saved} new saved.',
                'total_fetched': total,
                'saved_count': saved,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'POST required'})


@csrf_exempt
@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
def fetch_news_now(request):
    """Used by the enhanced dashboard fetch form."""
    if request.method == 'POST':
        try:
            categories = request.POST.getlist('categories') or ['news', 'sport', 'entertainment']
            sources = request.POST.getlist('sources') or ['google', 'google_nigeria']
            limit = int(request.POST.get('limit_per_source', 3))
            auto_save = request.POST.get('auto_save') == 'true'

            from blog.ai_service import EnhancedNewsFetcher
            fetcher = EnhancedNewsFetcher()
            articles = fetcher.fetch_multiple_sources(
                categories=categories,
                sources=sources,
                limit_per_source=limit
            )

            saved_count = 0
            if auto_save:
                for article in articles:
                    url = article.get('url', '')
                    if url and not NewsArticle.objects.filter(url=url).exists():
                        NewsArticle.objects.create(
                            title=article['title'][:499],
                            content=article.get('content', '')[:5000],
                            summary=article.get('description', '')[:500],
                            url=url,
                            source=article.get('source', 'Unknown'),
                            category=article.get('category', 'NEWS'),
                            image_url=article.get('image_url', ''),
                            published_at=timezone.now(),
                        )
                        saved_count += 1

            return JsonResponse({
                'success': True,
                'message': f'Fetched {len(articles)} articles' + (f', saved {saved_count}' if auto_save else ''),
                'articles': articles,
                'saved_count': saved_count,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
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
                post = fetcher.generate_blog_post_from_article({
                    'title': article.title,
                    'description': article.summary,
                    'content': article.content,
                    'url': article.url,
                    'source': article.source,
                    'category': article.category,
                    'published_at': article.published_at.isoformat() if article.published_at else None,
                })
                if post:
                    article.created_as_post = True
                    article.save()
                    created_count += 1

            return JsonResponse({'success': True, 'message': f'Generated {created_count} blog posts'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
def dashboard_stats(request):
    return JsonResponse({
        'total_articles': NewsArticle.objects.count(),
        'today_articles': NewsArticle.objects.filter(imported_at__date=timezone.now().date()).count(),
        'auto_posts': Post.objects.filter(title__startswith='[News]').count(),
        'to_process': NewsArticle.objects.filter(created_as_post=False).count(),
    })


@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
def convert_to_post(request, article_id):
    try:
        article = NewsArticle.objects.get(id=article_id)
        from blog.ai_service import EnhancedNewsFetcher
        fetcher = EnhancedNewsFetcher()
        post = fetcher.generate_blog_post_from_article({
            'title': article.title,
            'description': article.summary,
            'content': article.content,
            'url': article.url,
            'source': article.source,
            'category': article.category,
            'published_at': article.published_at.isoformat() if article.published_at else None,
        })
        if post:
            article.created_as_post = True
            article.save()
            return JsonResponse({'success': True, 'message': f'Created post: {post.title}'})
        return JsonResponse({'success': False, 'message': 'Failed to create post'})
    except NewsArticle.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Article not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@csrf_exempt
@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
def post_article(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            article = data.get('article')
            if not article:
                return JsonResponse({'success': False, 'message': 'No article data provided'})

            from django.utils.text import slugify
            from django.contrib.auth.models import User

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

            post = Post.objects.create(
                title=article['title'][:200],
                slug=slug,
                content=article.get('content', article.get('description', ''))[:5000],
                excerpt=article.get('description', '')[:200],
                author=author,
                category=category_obj,
                featured_image=article.get('image_url', ''),
                published_date=timezone.now(),
                is_featured=data.get('is_featured', False)
            )
            tags = data.get('tags', ['news'])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',')]
            for tag in tags:
                post.tags.add(tag.strip())

            url = article.get('url', '')
            if data.get('save_article', True) and url and not NewsArticle.objects.filter(url=url).exists():
                NewsArticle.objects.create(
                    title=article['title'][:499],
                    content=article.get('content', '')[:5000],
                    summary=article.get('description', '')[:500],
                    url=url,
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
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
def post_multiple_articles(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            articles = data.get('articles', [])
            posted_count = 0
            post_titles = []

            from django.utils.text import slugify
            from django.contrib.auth.models import User

            for article in articles:
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

                post = Post.objects.create(
                    title=article['title'][:200],
                    slug=slug,
                    content=article.get('content', article.get('description', ''))[:5000],
                    excerpt=article.get('description', '')[:200],
                    author=author,
                    category=category_obj,
                    featured_image=article.get('image_url', ''),
                    published_date=timezone.now(),
                )
                tags = data.get('tags', ['news'])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(',')]
                for tag in tags:
                    post.tags.add(tag.strip())

                posted_count += 1
                post_titles.append(post.title)

            return JsonResponse({
                'success': True,
                'message': f'Posted {posted_count} articles',
                'posted_count': posted_count,
                'post_titles': post_titles,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
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
@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
def update_post_image(request):
    if request.method == 'POST':
        try:
            post_id = request.POST.get('post_id')
            post = Post.objects.get(id=post_id)

            if request.POST.get('use_default') == 'true':
                post.featured_image = 'blog_images/default.jpg'
                post.save()
                return JsonResponse({'success': True, 'message': 'Default image set', 'image_url': '/media/blog_images/default.jpg'})

            if 'image' in request.FILES:
                image_file = request.FILES['image']
                if image_file.size > 5 * 1024 * 1024:
                    return JsonResponse({'success': False, 'message': 'File too large (max 5MB)'})
                file_name = default_storage.save(f'blog_images/{post.slug}_{image_file.name}', ContentFile(image_file.read()))
                post.featured_image.name = file_name
                post.save()
                return JsonResponse({'success': True, 'message': 'Image uploaded', 'image_url': f'/media/{file_name}'})

            image_url = request.POST.get('image_url')
            if image_url:
                post.featured_image = image_url
                post.save()
                return JsonResponse({'success': True, 'message': 'Image URL saved', 'image_url': image_url})

            return JsonResponse({'success': False, 'message': 'No image provided'})
        except Post.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Post not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
def remove_post_image(request, post_id):
    if request.method == 'POST':
        try:
            post = Post.objects.get(id=post_id)
            post.featured_image = None
            post.save()
            return JsonResponse({'success': True, 'message': 'Image removed'})
        except Post.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Post not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
def delete_news_article(request, article_id):
    if request.method == 'DELETE':
        try:
            NewsArticle.objects.get(id=article_id).delete()
            return JsonResponse({'success': True, 'message': 'Article deleted'})
        except NewsArticle.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Article not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
def delete_post(request, post_id):
    if request.method == 'DELETE':
        try:
            Post.objects.get(id=post_id).delete()
            return JsonResponse({'success': True, 'message': 'Post deleted'})
        except Post.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Post not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@csrf_exempt
@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
def fetch_article_image(request):
    """
    Given an article URL, scrape and return the best image (og:image first).
    Called from dashboard JS to auto-fill images for articles that have none.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            url = data.get('url', '').strip()
            if not url:
                return JsonResponse({'success': False, 'message': 'No URL provided'})

            from blog.ai_service import EnhancedNewsFetcher
            # Use scrape_article which gets og:image reliably
            scraped = EnhancedNewsFetcher.scrape_article(url)
            image_url = scraped.get('image_url', '')

            if image_url:
                return JsonResponse({'success': True, 'image_url': image_url})
            return JsonResponse({'success': False, 'message': 'No image found'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'POST required'})


@csrf_exempt
@login_required(login_url='/admin/login/')
@user_passes_test(is_staff, login_url='/admin/login/')
def generate_roundup(request):
    """
    Generate a news roundup post for a given category and type (foreign/nigeria).
    Called by the dashboard Generate buttons.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            news_type = data.get('type', 'nigeria')   # 'foreign' or 'nigeria'
            category  = data.get('category', 'news')

            from blog.ai_service import EnhancedNewsFetcher
            post, error = EnhancedNewsFetcher.generate_roundup_post(
                category=category,
                news_type=news_type,
                limit=8,
            )

            if post:
                # Save articles to NewsArticle for record-keeping
                return JsonResponse({
                    'success': True,
                    'post_title': post.title,
                    'post_url': f'/post/{post.slug}/',
                    'story_count': post.content.count('<div style="padding:1rem'),
                })
            return JsonResponse({'success': False, 'message': error or 'Failed to generate post'})

        except Exception as e:
            import traceback; traceback.print_exc()
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'POST required'})