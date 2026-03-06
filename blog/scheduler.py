# blog/scheduler.py
import logging
logger = logging.getLogger(__name__)


def fetch_latest_news_job():
    """
    Runs every 2 hours — fetches latest Nigerian news from all sources.
    Priority order: Google News Nigeria → Nigerian RSS → BBC international.
    """
    try:
        from blog.models import NewsArticle
        from blog.ai_service import EnhancedNewsFetcher
        from django.utils import timezone

        logger.info("⏰ Scheduled news fetch starting...")
        articles = EnhancedNewsFetcher.fetch_latest_nigerian_news(limit_per_source=5)

        saved = 0
        for article in articles:
            url = article.get('url', '').strip()
            if not url or NewsArticle.objects.filter(url=url).exists():
                continue
            try:
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
            except Exception as e:
                logger.warning(f"Could not save article: {e}")

        logger.info(f"✅ Done: {len(articles)} fetched, {saved} new saved.")

    except Exception as e:
        logger.error(f"❌ Scheduled fetch failed: {e}")


def start():
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            fetch_latest_news_job,
            trigger=IntervalTrigger(hours=2),
            id='fetch_latest_news',
            name='Fetch latest Nigerian news every 2 hours',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()
        logger.info("🕐 News scheduler started — every 2 hours.")

    except ImportError:
        logger.warning("⚠️ apscheduler not installed. Run: pip install apscheduler")
    except Exception as e:
        logger.warning(f"⚠️ Scheduler failed to start: {e}")