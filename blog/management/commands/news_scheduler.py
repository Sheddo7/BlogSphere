# blog/management/commands/news_scheduler.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from blog.models import NewsArticle, Category, Post
from blog.ai_service import EnhancedNewsFetcher
from django.contrib.auth.models import User
import logging
import sys

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Schedule and manage automated news fetching'

    def add_arguments(self, parser):
        parser.add_argument('--action', type=str, default='start',
                            choices=['start', 'stop', 'status', 'test'],
                            help='Action to perform')
        parser.add_argument('--categories', type=str, default='news,sport,entertainment',
                            help='Comma-separated list of categories')
        parser.add_argument('--sources', type=str, default='google,reddit,bbc',
                            help='Comma-separated list of sources')
        parser.add_argument('--auto-create', action='store_true',
                            help='Automatically create blog posts')
        parser.add_argument('--limit', type=int, default=3,
                            help='Articles per source/category')

    def handle(self, *args, **options):
        action = options['action']

        if action == 'start':
            self.start_scheduler(
                options['categories'],
                options['sources'],
                options['auto_create'],
                options['limit']
            )
        elif action == 'test':
            self.test_fetching(
                options['categories'],
                options['sources'],
                options['limit']
            )
        elif action == 'status':
            self.check_status()
        elif action == 'stop':
            self.stop_scheduler()

    def start_scheduler(self, categories_str, sources_str, auto_create, limit):
        """Start the news scheduler"""
        self.stdout.write(self.style.SUCCESS('🚀 Starting news scheduler...'))

        categories = categories_str.split(',')
        sources = sources_str.split(',')

        # For now, just run once
        self.fetch_and_process_news(categories, sources, auto_create, limit)

        self.stdout.write(self.style.SUCCESS('✅ Scheduler started (single run for now)!'))
        self.stdout.write(self.style.SUCCESS('📝 To schedule automatic runs, install django-apscheduler'))

    def fetch_and_process_news(self, categories, sources, auto_create, limit):
        """Fetch and process news from multiple sources"""
        self.stdout.write(self.style.SUCCESS(f'🔄 Fetching news from {len(sources)} sources...'))

        fetcher = EnhancedNewsFetcher()
        all_articles = fetcher.fetch_multiple_sources(categories, sources, limit)

        saved_count = 0
        for article in all_articles:
            try:
                # Check if article already exists
                if NewsArticle.objects.filter(url=article['url']).exists():
                    continue

                # Parse date
                pub_date = self.parse_date(article.get('published_at'))

                # Create NewsArticle
                news_article = NewsArticle.objects.create(
                    title=article['title'][:499],
                    content=article.get('content', article.get('description', ''))[:5000],
                    summary=article.get('description', '')[:500],
                    url=article['url'],
                    source=article.get('source', 'Unknown'),
                    category=article.get('category', 'NEWS'),
                    image_url=article.get('image_url', ''),
                    published_at=pub_date,
                )

                saved_count += 1

                # Auto-create blog post if enabled
                if auto_create and saved_count <= 3:  # Limit to 3 auto-posts per fetch
                    fetcher.generate_blog_post_from_article(article)
                    self.stdout.write(f'📝 Created blog post from: {article["title"][:50]}...')

            except Exception as e:
                logger.error(f"Error saving article: {e}")
                self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)[:100]}'))

        self.stdout.write(self.style.SUCCESS(f'✅ Saved {saved_count} new articles'))
        return saved_count

    def generate_daily_posts(self):
        """Generate blog posts from recent news articles"""
        self.stdout.write(self.style.SUCCESS('🤖 Generating daily blog posts...'))

        # Get articles from last 24 hours that haven't been converted
        yesterday = timezone.now() - timedelta(days=1)
        articles = NewsArticle.objects.filter(
            created_as_post=False,
            published_at__gte=yesterday
        ).order_by('-published_at')[:10]  # Top 10 articles

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
                self.stdout.write(f'✅ Created: {post.title[:50]}...')

        self.stdout.write(self.style.SUCCESS(f'🎉 Generated {created_count} blog posts'))
        return created_count

    def parse_date(self, date_str):
        """Parse various date formats"""
        if not date_str:
            return timezone.now()

        try:
            # Try common formats
            formats = [
                '%a, %d %b %Y %H:%M:%S %Z',
                '%a, %d %b %Y %H:%M:%S %z',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            # If all fail, return now
            return timezone.now()
        except:
            return timezone.now()

    def test_fetching(self, categories_str, sources_str, limit):
        """Test news fetching without saving"""
        self.stdout.write(self.style.SUCCESS('🧪 Testing news fetching...'))

        categories = categories_str.split(',')
        sources = sources_str.split(',')

        fetcher = EnhancedNewsFetcher()
        articles = fetcher.fetch_multiple_sources(categories, sources, limit)

        self.stdout.write(self.style.SUCCESS(f'📊 Found {len(articles)} articles:'))

        for i, article in enumerate(articles[:5], 1):  # Show first 5
            self.stdout.write(f'{i}. {article["title"][:80]}...')
            self.stdout.write(f'   Source: {article.get("source")} | Category: {article.get("category")}')
            self.stdout.write(f'   URL: {article.get("url")[:80]}...')

        return articles

    def check_status(self):
        """Check news system status"""
        total_articles = NewsArticle.objects.count()
        today_articles = NewsArticle.objects.filter(
            imported_at__date=timezone.now().date()
        ).count()

        self.stdout.write(self.style.SUCCESS(f'📊 News System Status:'))
        self.stdout.write(f'Total articles: {total_articles}')
        self.stdout.write(f"Today's articles: {today_articles}")
        self.stdout.write(f'Articles converted to posts: {NewsArticle.objects.filter(created_as_post=True).count()}')
        self.stdout.write(f'News sources available: Google News, Reddit, BBC, NewsAPI')

        # Check NewsAPI key
        from django.conf import settings
        api_key = getattr(settings, 'NEWS_API_KEY', '')
        if api_key:
            self.stdout.write(self.style.SUCCESS('✅ NewsAPI key is set'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  NewsAPI key is not set'))

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.stdout.write(self.style.SUCCESS('🛑 Scheduler stopped (manual run only for now)'))