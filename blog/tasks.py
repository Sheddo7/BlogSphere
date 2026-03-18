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
    print("🤖 Generating AI posts...")
    yesterday = timezone.now() - timezone.timedelta(days=1)
    articles = NewsArticle.objects.filter(
        created_as_post=False,
        published_at__gte=yesterday
    )[:10]

    from blog.ai_service import EnhancedNewsFetcher
    from django.contrib.auth.models import User

    created_count = 0
    for article in articles:
        if Post.objects.filter(title__icontains=article.title[:50]).exists():
            continue

        article_dict = {
            'title': article.title,
            'description': article.summary,
            'content': article.content,
            'url': article.url,
            'source': article.source,
            'category': article.category,
        }

        post = EnhancedNewsFetcher.generate_blog_post_from_article(article_dict)
        if post:
            article.created_as_post = True
            article.save()
            created_count += 1

    return f"Created {created_count} AI posts"