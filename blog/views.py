# blog/views.py - COMPLETE UPDATED VERSION WITH ALL FUNCTIONS
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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from blog.ai_service import TogetherService


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

    # Get recent posts
    recent_posts = Post.objects.order_by('-published_date')[:10]

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
            # Get categories and sources from POST data
            categories = request.POST.getlist('categories', ['news', 'sport', 'entertainment'])
            sources = request.POST.getlist('sources', ['google', 'reddit'])
            limit_per_source = int(request.POST.get('limit_per_source', 3))

            # Import and use the enhanced news fetcher
            from blog.ai_service import EnhancedNewsFetcher
            fetcher = EnhancedNewsFetcher()
            articles = fetcher.fetch_multiple_sources(
                categories=categories,
                sources=sources,
                limit_per_source=limit_per_source
            )

            # Save articles if auto_save is enabled
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
        })


# ===== NEW API ENDPOINTS =====


@csrf_exempt
@login_required
@user_passes_test(is_staff)
def post_article(request):
    """Post article with AI content generation – now handles None safely."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            article = data.get('article')

            if not article:
                return JsonResponse({'success': False, 'message': 'No article data provided'})

            # Get or create category
            category_name = article.get('category', 'NEWS')
            from django.utils.text import slugify
            from django.contrib.auth.models import User

            category_obj, created = Category.objects.get_or_create(name=category_name)

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

            # === AI PROCESSING ===
            print(f"\n🤖 AI PROCESSING START")
            print(f"Title: {article['title'][:60]}")
            print(f"URL: {article.get('url', '')[:60]}")

            from blog.ai_service import EnhancedNewsFetcher

            # Process with AI (scrape + paraphrase)
            processed_article = EnhancedNewsFetcher.process_article_with_ai(article)

            # CRITICAL: If processing failed, return error
            if processed_article is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Could not scrape original article content. Cannot post.'
                })

            # Use AI-generated content (safe because we checked for None)
            article_content = processed_article.get('content', article.get('description', ''))
            article_description = processed_article.get('description', article.get('description', ''))[:200]
            word_count = processed_article.get('word_count', 0)
            ai_processed = processed_article.get('ai_processed', False)

            print(f"✅ AI Processing complete: {word_count} words, AI={ai_processed}")
            # === END AI PROCESSING ===

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

            if ai_processed:
                post.tags.add('ai-rewritten')

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
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def post_multiple_articles(request):
    """Post multiple articles at once"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            articles = data.get('articles', [])

            posted_count = 0
            post_titles = []

            for article in articles:
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

                # Create blog post
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

                # Add tags (without auto-generated)
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
    """Get post details for editing"""
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
    """Update post's featured image"""
    if request.method == 'POST':
        try:
            post_id = request.POST.get('post_id')
            use_default = request.POST.get('use_default') == 'true'

            post = Post.objects.get(id=post_id)

            if use_default:
                # Use default image
                post.featured_image = 'blog_images/default.jpg'
                post.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Default image set successfully',
                    'image_url': '/media/blog_images/default.jpg'
                })

            # Handle uploaded file
            if 'image' in request.FILES:
                image_file = request.FILES['image']
                # Validate file size (5MB limit)
                if image_file.size > 5 * 1024 * 1024:
                    return JsonResponse({'success': False, 'message': 'File size too large (max 5MB)'})

                # Save file
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

            # Handle image URL
            image_url = request.POST.get('image_url')
            if image_url:
                # For now, just save the URL
                # In production, you might want to download and save the image
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
    """Remove post's featured image"""
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
    """Delete a news article"""
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
    """Delete a blog post"""
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




@csrf_exempt
@login_required
@user_passes_test(is_staff)
def together_chat(request):
    """
    API endpoint for direct Together.ai interactions.
    POST with JSON: {"message": "your prompt", "temperature": 0.7 (optional)}
    Returns: {"success": true, "content": "response text", "word_count": 123}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        temperature = float(data.get('temperature', 0.7))

        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)

        service = TogetherService()
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



# Backward compatibility alias
auto_fetch_news = fetch_news_now