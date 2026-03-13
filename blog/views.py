# blog/views.py - COMPLETE WITH DRAFT WORKFLOW
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import logging

from .models import Post, Category, NewsArticle
from django.core.paginator import Paginator
from .ai_service import EnhancedNewsFetcher, OpenRouterService

logger = logging.getLogger(__name__)

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
    """Individual post detail view (comments removed)"""
    post = get_object_or_404(Post, slug=slug)
    post.views += 1
    post.save()
    related_posts = Post.objects.filter(category=post.category).exclude(id=post.id)[:3]
    context = {
        'post': post,
        'related_posts': related_posts,
    }
    return render(request, 'blog/post_detail.html', context)


def category_posts(request, slug):
    """Category posts listing view"""
    try:
        category = get_object_or_404(Category, slug=slug)
        posts_list = Post.objects.filter(category=category)
        paginator = Paginator(posts_list, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        # Get all categories for the "Other categories" navigation
        categories = Category.objects.annotate(post_count=Count('posts')).order_by('-post_count')
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
    """Simple dashboard to view fetched news (kept for backward compatibility)"""
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


# ===== STAFF ONLY HELPER =====

def is_staff(user):
    return user.is_staff


# ===== ENHANCED / COMBINED DASHBOARD =====

@login_required
@user_passes_test(is_staff)
def combined_dashboard(request):
    """Single dashboard with all stats, drafts, recent articles, posts, fetch form, and scheduled jobs."""
    # Stats
    total_articles = NewsArticle.objects.count()
    today_articles = NewsArticle.objects.filter(imported_at__date=timezone.now().date()).count()
    auto_posts = Post.objects.filter(title__startswith='[News]').count()
    to_process = NewsArticle.objects.filter(status='draft').count()

    # Recent articles (all)
    recent_articles = NewsArticle.objects.order_by('-imported_at')[:20]

    # Drafts
    draft_articles = NewsArticle.objects.filter(status='draft').order_by('-imported_at')[:10]

    # Recent posts
    recent_posts = Post.objects.order_by('-published_date')[:10]

    # Categories
    categories = Category.objects.all()

    # Category stats
    category_stats = NewsArticle.objects.values('category').annotate(count=Count('id')).order_by('-count')

    # Mock scheduled jobs (replace with real data if you have a scheduler)
    scheduled_jobs = [
        {'id': 1, 'name': 'Hourly News Fetch', 'schedule': 'Every hour', 'last_run': timezone.now() - timezone.timedelta(minutes=30), 'next_run': timezone.now() + timezone.timedelta(minutes=30), 'is_active': True},
        {'id': 2, 'name': 'Daily Post Generation', 'schedule': '9:00 AM daily', 'last_run': timezone.now() - timezone.timedelta(hours=15), 'next_run': timezone.now() + timezone.timedelta(hours=9), 'is_active': True},
    ]

    context = {
        'stats': {
            'total_articles': total_articles,
            'today_articles': today_articles,
            'auto_posts': auto_posts,
            'to_process': to_process,
        },
        'recent_articles': recent_articles,
        'draft_articles': draft_articles,
        'recent_posts': recent_posts,
        'categories': categories,
        'category_stats': category_stats,
        'scheduled_jobs': scheduled_jobs,
    }
    return render(request, 'blog/combined_dashboard.html', context)


# ===== FETCH NEWS (modified to save drafts) =====

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def fetch_news_now(request):
    """Fetch news and save as drafts after AI processing."""
    if request.method == 'POST':
        try:
            categories = request.POST.getlist('categories', ['news', 'sport', 'entertainment'])
            sources = request.POST.getlist('sources', ['google', 'reddit'])
            limit_per_source = int(request.POST.get('limit_per_source', 3))

            fetcher = EnhancedNewsFetcher()
            articles = fetcher.fetch_multiple_sources(
                categories=categories,
                sources=sources,
                limit_per_source=limit_per_source
            )

            saved_count = 0
            for article in articles:
                if not NewsArticle.objects.filter(url=article['url']).exists():
                    processed = EnhancedNewsFetcher.process_article_with_ai(article)
                    if processed:
                        NewsArticle.objects.create(
                            title=article['title'][:499],
                            content=article.get('content', '')[:5000],
                            paraphrased_content=processed.get('content', '')[:5000],
                            summary=processed.get('description', '')[:500],
                            url=article['url'],
                            source=article.get('source', 'Unknown'),
                            category=article.get('category', 'NEWS'),
                            image_url=article.get('image_url', ''),
                            published_at=timezone.now(),
                            status='draft'
                        )
                        saved_count += 1

            return JsonResponse({
                'success': True,
                'message': f'Fetched {len(articles)} articles, saved {saved_count} as drafts.',
                'articles': articles,
                'saved_count': saved_count
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})


# ===== DRAFT API ENDPOINTS =====

@login_required
@user_passes_test(is_staff)
def get_draft(request, draft_id):
    """Get a single draft for editing."""
    try:
        draft = NewsArticle.objects.get(id=draft_id)
        return JsonResponse({
            'success': True,
            'id': draft.id,
            'title': draft.title,
            'content': draft.paraphrased_content or draft.content,
            'summary': draft.summary,
            'source': draft.source,
            'category': draft.category,
            'url': draft.url,
            'image_url': draft.image_url,
        })
    except NewsArticle.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Draft not found'})


@csrf_exempt
@login_required
@user_passes_test(is_staff)
def update_draft(request):
    """Update an existing draft with edited content."""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            draft = NewsArticle.objects.get(id=data['id'])
            draft.title = data['title']
            draft.paraphrased_content = data['content']
            draft.summary = data['summary']
            draft.source = data['source']
            draft.category = data['category']
            draft.url = data['url']
            draft.image_url = data['image_url']
            draft.save()
            return JsonResponse({'success': True})
        except NewsArticle.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Draft not found'})
    return JsonResponse({'success': False, 'message': 'Invalid method'})


@csrf_exempt
@login_required
@user_passes_test(is_staff)
def publish_draft(request):
    """Publish a draft as a blog post."""
    if request.method == 'POST':
        data = json.loads(request.body)
        draft = get_object_or_404(NewsArticle, id=data['id'])
        post = EnhancedNewsFetcher.generate_blog_post_from_article({
            'title': draft.title,
            'description': draft.summary,
            'content': draft.paraphrased_content or draft.content,
            'url': draft.url,
            'source': draft.source,
            'category': draft.category,
            'image_url': draft.image_url,
        })
        if post:
            draft.status = 'published'
            draft.created_as_post = True
            draft.save()
            return JsonResponse({'success': True, 'post_title': post.title})
        else:
            return JsonResponse({'success': False, 'message': 'Failed to create post'})
    return JsonResponse({'success': False, 'message': 'Invalid method'})


@login_required
@user_passes_test(is_staff)
def delete_draft(request, draft_id):
    """Delete a draft."""
    if request.method == 'DELETE':
        try:
            draft = NewsArticle.objects.get(id=draft_id)
            draft.delete()
            return JsonResponse({'success': True})
        except NewsArticle.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Draft not found'})
    return JsonResponse({'success': False, 'message': 'Invalid method'})


# ===== POST ARTICLE (original, kept for compatibility) =====

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
                content=article_content,
                excerpt=article_description,
                author=author,
                category=category_obj,
                featured_image=article.get('image_url', ''),
                published_date=timezone.now(),
                is_featured=data.get('is_featured', False)
            )

            tags = data.get('tags', ['news'])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',')]
            for tag in tags:
                post.tags.add(tag.strip())

            if data.get('save_article', True):
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
    """Post multiple articles at once."""
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
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@csrf_exempt
@login_required
@user_passes_test(is_staff)
def get_post(request, post_id):
    """Get post details for editing."""
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
    """Update post's featured image."""
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
    """Remove post's featured image."""
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
    """Delete a news article."""
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
    """Delete a blog post."""
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


# ===== OPENROUTER CHAT =====

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def openrouter_chat(request):
    """API endpoint for direct OpenRouter interactions."""
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


# ===== PREVIEW ARTICLE =====

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

            processed = EnhancedNewsFetcher.process_article_with_ai(article)
            if processed is None:
                return JsonResponse({'success': False, 'message': 'Could not generate preview (scraping failed)'})

            content = processed.get('content', '')
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
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


# Backward compatibility alias
auto_fetch_news = fetch_news_now