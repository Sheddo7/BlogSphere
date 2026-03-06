# blog/scheduler.py
import logging
logger = logging.getLogger(__name__)


def fetch_latest_news_job():
    """Runs every 2 hours — fetches latest news across all categories."""
    try:
        from blog.models import NewsArticle
        from blog.ai_service import EnhancedNewsFetcher
        from django.utils import timezone

        fetcher = EnhancedNewsFetcher()
        articles = fetcher.fetch_multiple_sources(
            categories=['news', 'sport', 'entertainment', 'economy', 'politics', 'technology'],
            sources=['google', 'google_nigeria', 'punch', 'vanguard', 'channels'],
            limit_per_source=5
        )

        saved = 0
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
                saved += 1

        logger.info(f"✅ Scheduled fetch: {len(articles)} fetched, {saved} new saved.")

    except Exception as e:
        logger.error(f"❌ Scheduled news fetch failed: {e}")


def start():
    """Start the APScheduler background scheduler."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            fetch_latest_news_job,
            trigger=IntervalTrigger(hours=2),
            id='fetch_latest_news',
            name='Fetch latest news every 2 hours',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()
        logger.info("🕐 News scheduler started — runs every 2 hours.")

    except ImportError:
        logger.warning("⚠️ apscheduler not installed. Run: pip install apscheduler")
    except Exception as e:
        logger.warning(f"⚠️ Scheduler failed to start: {e}")