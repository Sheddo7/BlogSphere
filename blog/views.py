# blog/views.py - COMPLETE UPDATED VERSION WITH NIGERIAN PRIORITY AND DEBUG VIEW
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import requests
import feedparser
from bs4 import BeautifulSoup

from .models import Post, Category, Comment, NewsArticle
from django.core.paginator import Paginator
from blog.ai_service import EnhancedNewsFetcher   # for debug view


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

    # Mock scheduled jobs (for demo)
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
    """AJAX endpoint to fetch news immediately – Nigerian sources prioritized."""
    if request.method == 'POST':
        try:
            # Default: all categories, Nigerian sources first
            categories = request.POST.getlist('categories', ['news', 'sport', 'entertainment', 'economy', 'politics', 'technology'])
            sources = request.POST.getlist('sources', ['punch', 'vanguard', 'channels', 'newsapi', 'bbc', 'reddit'])
            limit_per_source = int(request.POST.get('limit_per_source', 5))

            from blog.ai_service import EnhancedNewsFetcher
            articles = EnhancedNewsFetcher.fetch_multiple_sources(
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
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

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

                post = EnhancedNewsFetcher.generate_blog_post_from_article(article_dict)
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

        article_dict = {
            'title': article.title,
            'description': article.summary,
            'content': article.content,
            'url': article.url,
            'source': article.source,
            'category': article.category,
            'published_at': article.published_at.isoformat() if article.published_at else None,
        }

        post = EnhancedNewsFetcher.generate_blog_post_from_article(article_dict)
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
        })


# ===== NEW API ENDPOINTS =====

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def post_article(request):
    """Post a single article with AI processing. Now includes error handling."""
    if request.method == 'POST':
        try:
            # Parse JSON with error handling
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON'})

            article = data.get('article')
            if not article:
                return JsonResponse({'success': False, 'message': 'No article data provided'})

            # Ensure article is a dict
            if not isinstance(article, dict):
                return JsonResponse({'success': False, 'message': 'Article must be an object'})

            # Get or create category
            category_name = article.get('category', 'NEWS')
            from django.utils.text import slugify
            from django.contrib.auth.models import User

            category_obj, created = Category.objects.get_or_create(
                name=category_name
            )

            # Get admin user
            try:
                author = User.objects.get(username='admin')
            except User.DoesNotExist:
                author = User.objects.first()

            # Generate slug
            base_slug = slugify(article['title'][:50])
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Process article with AI
            print(f"🤖 Processing article with AI: {article['title'][:60]}...")
            from blog.ai_service import EnhancedNewsFetcher

            processed_article = EnhancedNewsFetcher.process_article_with_ai(article)
            if processed_article is None:
                processed_article = article  # fallback

            article_content = processed_article.get('content', article.get('description', ''))
            article_description = processed_article.get('description', article.get('description', ''))[:200]

            print(f"✅ Content processed: {processed_article.get('word_count', 0)} words")

            # Create blog post
            post = Post.objects.create(
                title=article['title'][:200],
                slug=slug,
                content=article_content,
                excerpt=article_description,
                author=author,
                category=category_obj,
                featured_image=article.get('image_url', ''),
                published_date=timezone.now(),
                is_featured=data.get('is_featured', False)
            )

            # Add tags
            tags = data.get('tags', ['news'])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',')]
            for tag in tags:
                post.tags.add(tag.strip())

            if processed_article.get('ai_processed'):
                post.tags.add('ai-rewritten')

            # Save as NewsArticle if requested
            if data.get('save_article', True):
                if not NewsArticle.objects.filter(url=article.get('url', '')).exists():
                    NewsArticle.objects.create(
                        title=article['title'][:499],
                        content=processed_article.get('content', '')[:5000],
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
                'word_count': processed_article.get('word_count', 0),
                'ai_processed': processed_article.get('ai_processed', False),
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

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

                category_obj, created = Category.objects.get_or_create(
                    name=category_name
                )

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
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

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
            return JsonResponse({
                'success': True,
                'message': 'Image removed successfully'
            })
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
            return JsonResponse({
                'success': True,
                'message': 'Article deleted successfully'
            })
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
            return JsonResponse({
                'success': True,
                'message': 'Post deleted successfully'
            })
        except Post.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Post not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


# ===== DIAGNOSTIC VIEW FOR NIGERIAN RSS FEEDS =====
@login_required
@user_passes_test(is_staff)
def debug_nigerian_feeds(request):
    """Check each Nigerian RSS feed and show raw response and feedparser results."""
    from blog.ai_service import EnhancedNewsFetcher
    import requests
    import feedparser

    sources = ['punch', 'vanguard', 'channels']
    categories = ['news', 'sport', 'entertainment', 'economy', 'politics']
    output = []

    for source in sources:
        output.append(f"\n{'='*60}")
        output.append(f"SOURCE: {source.upper()}")
        output.append('='*60)

        # Test main feed
        main_feed = EnhancedNewsFetcher.SOURCES[source].get('main_feed')
        if main_feed:
            output.append(f"\nMAIN FEED: {main_feed}")
            try:
                resp = requests.get(main_feed, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
                output.append(f"HTTP {resp.status_code}, Content-Length: {len(resp.text)}")
                if resp.status_code == 200:
                    # Show first 500 chars (sanitized)
                    preview = resp.text[:500].replace('\n', ' ').replace('\r', '')
                    output.append(f"Preview: {preview}")
                    # Parse with feedparser
                    feed = feedparser.parse(resp.text)
                    output.append(f"feedparser entries: {len(feed.entries)}")
                    if feed.entries:
                        output.append(f"First title: {feed.entries[0].title}")
                        output.append(f"First link: {feed.entries[0].link}")
                else:
                    output.append("Failed to fetch")
            except Exception as e:
                output.append(f"Error: {e}")

        # Test category feeds
        for cat in categories:
            feed_url = EnhancedNewsFetcher.SOURCES[source]['category_urls'].get(cat)
            if feed_url:
                output.append(f"\nCATEGORY {cat}: {feed_url}")
                try:
                    resp = requests.get(feed_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
                    output.append(f"  HTTP {resp.status_code}, Content-Length: {len(resp.text)}")
                    if resp.status_code == 200:
                        preview = resp.text[:300].replace('\n', ' ').replace('\r', '')
                        output.append(f"  Preview: {preview}")
                        feed = feedparser.parse(resp.text)
                        output.append(f"  feedparser entries: {len(feed.entries)}")
                        if feed.entries:
                            output.append(f"  First title: {feed.entries[0].title}")
                    else:
                        output.append("  Failed to fetch")
                except Exception as e:
                    output.append(f"  Error: {e}")

    return HttpResponse('<pre>' + '\n'.join(output) + '</pre>')


# Backward compatibility alias
auto_fetch_news = fetch_news_now