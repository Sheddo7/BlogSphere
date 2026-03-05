# blog/scheduler.py
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone

logger = logging.getLogger(__name__)

def fetch_latest_news_job():
    """
    Scheduled job: fetch latest news across all categories
    from multiple sources and save to database.
    Runs automatically every 2 hours.
    """
    try:
        from blog.ai_service import EnhancedNewsFetcher
        from blog.models import NewsArticle

        logger.info("⏰ Scheduled news fetch starting...")

        categories = ['news', 'sport', 'entertainment', 'economy', 'politics', 'technology']
        sources = ['google', 'google_nigeria', 'punch', 'vanguard', 'bbc']

        articles = EnhancedNewsFetcher.fetch_multiple_sources(
            categories=categories,
            sources=sources,
            limit_per_source=5
        )

        saved = 0
        for article in articles:
            if article.get('url') and not NewsArticle.objects.filter(url=article['url']).exists():
                NewsArticle.objects.create(
                    title=article.get('title', 'Untitled')[:499],
                    content=article.get('content', '')[:5000],
                    summary=article.get('description', '')[:500],
                    url=article.get('url', ''),
                    source=article.get('source', 'Unknown'),
                    category=article.get('category', 'NEWS'),
                    image_url=article.get('image_url', ''),
                    published_at=timezone.now(),
                )
                saved += 1

        logger.info(f"✅ Scheduled fetch done: {len(articles)} fetched, {saved} new saved.")

    except Exception as e:
        logger.error(f"❌ Scheduled news fetch failed: {e}")


def start():
    """Start the APScheduler background scheduler."""
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        fetch_latest_news_job,
        trigger=IntervalTrigger(hours=2),
        id="fetch_latest_news",
        name="Fetch latest news every 2 hours",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    logger.info("🕐 News scheduler started — fetching every 2 hours.")
    scheduler.start()