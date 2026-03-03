# blog/tasks.py
from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from blog.models import NewsArticle, Post
from blog.ai_service import NewsAIService

@shared_task
def fetch_latest_news():
    """Task to fetch latest news"""
    print("🔄 Fetching latest news...")
    call_command('fetch_news', '--source', 'newsapi', '--limit', '15')
    return "News fetched successfully"

@shared_task
def generate_ai_posts():
    """Task to generate blog posts from news articles"""
    print("🤖 Generating AI posts...")

    # Get unprocessed news articles from last 24 hours
    yesterday = timezone.now() - timezone.timedelta(days=1)
    articles = NewsArticle.objects.filter(
        processed=False,
        published_at__gte=yesterday
    )[:10]

    ai_service = NewsAIService()
    created_count = 0

    for article in articles:
        # Check if similar post already exists
        if Post.objects.filter(title__icontains=article.title[:50]).exists():
            continue

        # Convert to blog post (you can customize this)
        from django.contrib.auth.models import User
        try:
            author = User.objects.get(username='admin')
        except:
            author = User.objects.first()

        # Enhance content
        enhanced_content = ai_service.enhance_article_with_ai(article.content)

        # Create post
        Post.objects.create(
            title=f"News: {article.title}",
            slug=f"ai-news-{article.id}",
            content=enhanced_content,
            excerpt=article.summary[:150],
            author=author,
            category=article.categories.first(),
            featured_image=article.image_url or '',
            published_date=timezone.now(),
        )

        article.processed = True
        article.save()
        created_count += 1

    return f"Created {created_count} AI posts"