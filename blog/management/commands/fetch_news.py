# blog/management/commands/fetch_news.py - SIMPLE VERSION
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from blog.models import NewsArticle, Category, Post
from blog.ai_service import SimpleNewsFetcher
from django.contrib.auth.models import User
import hashlib

class Command(BaseCommand):
    help = 'Fetch news from various sources'

    def add_arguments(self, parser):
        parser.add_argument('--source', type=str, default='google',
                            choices=['google', 'reddit', 'newsapi', 'all'],
                            help='News source')
        parser.add_argument('--limit', type=int, default=5,
                            help='Number of articles to fetch')
        parser.add_argument('--auto-create', action='store_true',
                            help='Automatically create blog posts')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('📡 Starting news fetch...'))

        fetcher = SimpleNewsFetcher()
        source = options['source']
        limit = options['limit']

        news_items = []

        # Fetch based on source
        if source == 'google' or source == 'all':
            news_items.extend(fetcher.fetch_google_news_rss()[:limit])

        if source == 'reddit' or source == 'all':
            news_items.extend(fetcher.fetch_reddit_news(limit=limit))

        if source == 'newsapi' or source == 'all':
            # You'll need to set NEWS_API_KEY in environment
            news_items.extend(fetcher.fetch_newsapi())

        created_count = 0
        for item in news_items[:limit]:
            # Generate unique ID from URL
            url_hash = hashlib.md5(item['url'].encode()).hexdigest()[:32]

            # Check if already exists
            if NewsArticle.objects.filter(url=item['url']).exists():
                self.stdout.write(f'⏭️ Skipping duplicate: {item["title"][:50]}...')
                continue

            # Extract content if needed
            content = item.get('content') or item.get('description', '')
            if not content and 'url' in item:
                extracted = fetcher.extract_content_from_url(item['url'])
                if extracted:
                    content = extracted

            # Categorize
            category = fetcher.categorize_article(
                item.get('title', ''),
                item.get('description', '')
            )

            # Generate summary
            summary = fetcher.generate_summary(content)

            # Parse date
            pub_date = None
            if item.get('published_at'):
                try:
                    from dateutil import parser
                    pub_date = parser.parse(item['published_at'])
                except:
                    pub_date = timezone.now()
            else:
                pub_date = timezone.now()

            # Create news article
            try:
                news_article = NewsArticle.objects.create(
                    title=item.get('title', 'Untitled')[:499],
                    content=content[:5000],
                    summary=summary[:500],
                    url=item['url'],
                    source=item.get('source', 'Unknown'),
                    category=category,
                    image_url=item.get('image_url', ''),
                    published_at=pub_date,
                )

                self.stdout.write(
                    self.style.SUCCESS(f'✅ Saved: {news_article.title[:60]}...')
                )
                created_count += 1

                # Auto-create blog post if requested
                if options['auto_create']:
                    self.create_blog_post(news_article)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error: {str(e)[:100]}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Fetched {created_count} news articles!')
        )
        self.stdout.write(
            self.style.NOTICE(f'📊 View at: http://localhost:8000/admin/blog/newsarticle/')
        )

    def create_blog_post(self, news_article):
        """Convert news article to blog post"""
        # Check if already exists
        if Post.objects.filter(title=news_article.title).exists():
            return

        # Get admin user
        try:
            author = User.objects.get(username='admin')
        except User.DoesNotExist:
            author = User.objects.first()

        # Get or create category
        category_obj, _ = Category.objects.get_or_create(
            name=news_article.category
        )

        # Generate slug
        from django.utils.text import slugify
        base_slug = slugify(news_article.title)
        slug = base_slug
        counter = 1
        while Post.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Create post
        post = Post.objects.create(
            title=news_article.title,
            slug=slug,
            content=news_article.content,
            excerpt=news_article.summary[:200],
            author=author,
            category=category_obj,
            featured_image=news_article.image_url or '',
            published_date=news_article.published_at or timezone.now(),
        )

        # Add tags based on category
        post.tags.add(news_article.category.lower(), 'news', 'trending')

        # Mark as created
        news_article.created_as_post = True
        news_article.save()

        self.stdout.write(f'📝 Created blog post: {post.title[:50]}...')