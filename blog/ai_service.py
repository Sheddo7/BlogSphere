# blog/ai_service.py - FINAL VERSION (NO GOOGLE NEWS)
import os
import requests
import json
from datetime import datetime
import feedparser
from django.conf import settings
from django.utils import timezone
from bs4 import BeautifulSoup
import time
import re


class EnhancedNewsFetcher:
    """News fetcher using NewsAPI, Reddit, BBC and Nigerian RSS (NO GOOGLE)"""

    SOURCES = {
        'reddit': {
            'subreddits': {
                'news': 'news',
                'sport': 'sports',
                'entertainment': 'entertainment',
                'economy': 'economy',
                'politics': 'politics',
                'technology': 'technology',
            }
        },
        'newsapi': {
            'base_url': 'https://newsapi.org/v2',
            'categories': {
                'news': 'general',
                'sport': 'sports',
                'entertainment': 'entertainment',
                'economy': 'business',
                'politics': 'politics',
                'technology': 'technology',
            }
        },
        'bbc': {
            'base_url': 'http://feeds.bbci.co.uk',
            'category_urls': {
                'news': 'http://feeds.bbci.co.uk/news/rss.xml',
                'sport': 'http://feeds.bbci.co.uk/sport/rss.xml',
                'entertainment': 'http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml',
                'economy': 'http://feeds.bbci.co.uk/news/business/rss.xml',
                'technology': 'http://feeds.bbci.co.uk/news/technology/rss.xml',
                'politics': 'http://feeds.bbci.co.uk/news/politics/rss.xml',
            }
        },
        'punch': {
            'base_url': 'https://punchng.com',
            'category_urls': {
                'news': 'https://punchng.com/feed/',
                'sport': 'https://punchng.com/sports/feed/',
                'entertainment': 'https://punchng.com/entertainment/feed/',
                'economy': 'https://punchng.com/business/feed/',
                'politics': 'https://punchng.com/politics/feed/',
            }
        },
        'vanguard': {
            'base_url': 'https://www.vanguardngr.com',
            'category_urls': {
                'news': 'https://www.vanguardngr.com/feed/',
                'sport': 'https://www.vanguardngr.com/category/sports/feed/',
                'entertainment': 'https://www.vanguardngr.com/category/entertainment/feed/',
                'economy': 'https://www.vanguardngr.com/category/business/feed/',
                'politics': 'https://www.vanguardngr.com/category/politics/feed/',
            }
        },
        'channels': {
            'base_url': 'https://www.channelstv.com',
            'category_urls': {
                'news': 'https://www.channelstv.com/feed/',
                'sport': 'https://www.channelstv.com/category/sports/feed/',
                'entertainment': 'https://www.channelstv.com/category/entertainment/feed/',
                'politics': 'https://www.channelstv.com/category/politics/feed/',
            }
        }
    }

    # Expanded consent page markers
    CONSENT_MARKERS = [
        'before you continue',
        'accept all',
        'reject all',
        'consent.google.com',
        'cookies and data',
        'privacy settings',
        'deliver and maintain google services',
        'track outages',
        'measure audience engagement',
        'personalized content',
        'personalized ads',
        'g.co/privacytools'
    ]

    @staticmethod
    def scrape_full_article_content(url):
        """Scrape article content – returns None if consent page detected."""
        try:
            print(f"🔍 Scraping: {url[:80]}...")

            # Skip Google News URLs entirely
            if 'news.google.com' in url:
                print("⛔ Skipping Google News URL (consent risk)")
                return None

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            # Check for consent page
            text_lower = response.text.lower()
            for marker in EnhancedNewsFetcher.CONSENT_MARKERS:
                if marker in text_lower:
                    print(f"❌ Consent page detected (marker: {marker})")
                    return None

            soup = BeautifulSoup(response.content, 'html.parser')
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside',
                                 'iframe', 'noscript', 'form', 'button']):
                element.decompose()

            # Article content selectors
            selectors = [
                'article', '[class*="article-content"]', '[class*="post-content"]',
                '[class*="entry-content"]', '[class*="story-body"]', '[class*="article-body"]',
                'main', '[role="main"]'
            ]
            content_area = None
            for sel in selectors:
                elements = soup.select(sel)
                if elements:
                    content_area = elements[0]
                    break
            if not content_area:
                content_area = soup.body or soup

            paragraphs = content_area.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li'])
            text_parts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40]
            full_text = '\n\n'.join(text_parts)

            if len(full_text) < 300:
                print("⚠️  Content too short")
                return None

            return full_text[:12000]

        except Exception as e:
            print(f"❌ Scrape error: {e}")
            return None

    @staticmethod
    def summarize_and_rewrite_with_ai(title, content, source, category, min_words=500):
        """Same as before – unchanged."""
        # ... (keep your existing implementation)
        # For brevity, I'm not repeating it here – keep your current method.
        pass

    @staticmethod
    def process_article_with_ai(article_dict):
        """Process article: scrape + AI rewrite. Skip Google News URLs."""
        url = article_dict.get('url', '')
        if 'news.google.com' in url:
            print("⛔ Skipping Google News article (cannot scrape reliably)")
            article_dict['content'] = f"<p>This article is from Google News. <a href='{url}' target='_blank'>Read original</a></p>"
            article_dict['ai_processed'] = False
            return article_dict

        # ... rest of your existing processing logic
        # (scrape, call AI, etc.)

    # ===== FETCH METHODS =====

    @staticmethod
    def fetch_news_api(category='general', country='ng', limit=10):
        """Fetch from NewsAPI (Nigeria)."""
        api_key = getattr(settings, 'NEWS_API_KEY', os.environ.get('NEWS_API_KEY', ''))
        if not api_key:
            print("⚠️  NewsAPI key missing")
            return []
        try:
            params = {
                'apiKey': api_key,
                'category': category,
                'country': country,
                'pageSize': limit,
                'language': 'en'
            }
            resp = requests.get('https://newsapi.org/v2/top-headlines', params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                articles = []
                for a in data.get('articles', []):
                    articles.append({
                        'title': a.get('title', ''),
                        'description': a.get('description', ''),
                        'content': a.get('content', ''),
                        'url': a.get('url', ''),
                        'image_url': a.get('urlToImage', ''),
                        'published_at': a.get('publishedAt', ''),
                        'source': a.get('source', {}).get('name', 'NewsAPI'),
                        'category': category.upper(),
                    })
                return articles
            else:
                print(f"❌ NewsAPI error {resp.status_code}")
                return []
        except Exception as e:
            print(f"❌ NewsAPI exception: {e}")
            return []

    @staticmethod
    def fetch_nigerian_rss(source, category='news', limit=10):
        """Fetch from Punch, Vanguard, Channels."""
        if source not in ['punch', 'vanguard', 'channels']:
            return []
        feed_url = EnhancedNewsFetcher.SOURCES[source]['category_urls'].get(category)
        if not feed_url:
            return []
        feed = feedparser.parse(feed_url)
        items = []
        for entry in feed.entries[:limit]:
            items.append({
                'title': entry.title,
                'description': entry.get('summary', ''),
                'content': entry.get('summary', ''),
                'url': entry.link,
                'published_at': entry.get('published', ''),
                'source': source.capitalize(),
                'category': category.upper(),
            })
        return items

    @staticmethod
    def fetch_reddit_by_category(category='news', limit=10):
        """Fetch from Reddit."""
        subreddit = EnhancedNewsFetcher.SOURCES['reddit']['subreddits'].get(category, 'news')
        url = f'https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}'
        headers = {'User-agent': 'newsbot/1.0'}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = []
                for post in data['data']['children']:
                    p = post['data']
                    items.append({
                        'title': p['title'],
                        'description': p.get('selftext', '')[:200],
                        'content': p.get('selftext', ''),
                        'url': f"https://reddit.com{p['permalink']}",
                        'published_at': datetime.fromtimestamp(p['created_utc']).isoformat(),
                        'source': f"Reddit r/{subreddit}",
                        'category': category.upper(),
                    })
                return items
            else:
                return []
        except Exception as e:
            print(f"❌ Reddit error: {e}")
            return []

    @staticmethod
    def fetch_bbc_rss(category='news', limit=10):
        """Fetch from BBC."""
        feed_url = EnhancedNewsFetcher.SOURCES['bbc']['category_urls'].get(category, 'http://feeds.bbci.co.uk/news/rss.xml')
        feed = feedparser.parse(feed_url)
        items = []
        for entry in feed.entries[:limit]:
            items.append({
                'title': entry.title,
                'description': entry.get('summary', ''),
                'content': entry.get('summary', ''),
                'url': entry.link,
                'published_at': entry.get('published', ''),
                'source': 'BBC',
                'category': category.upper(),
            })
        return items

    @staticmethod
    def fetch_multiple_sources(categories=None, sources=None, limit_per_source=5):
        """Fetch from multiple sources (NO GOOGLE)."""
        if categories is None:
            categories = ['news', 'sport', 'entertainment', 'economy', 'politics', 'technology']
        if sources is None:
            sources = ['newsapi', 'bbc', 'punch', 'vanguard', 'channels', 'reddit']

        all_articles = []
        for source in sources:
            for cat in categories:
                print(f"📡 {source}/{cat}...")
                if source == 'newsapi':
                    newsapi_cat = EnhancedNewsFetcher.SOURCES['newsapi']['categories'].get(cat, 'general')
                    arts = EnhancedNewsFetcher.fetch_news_api(newsapi_cat, 'ng', limit_per_source)
                elif source == 'reddit':
                    arts = EnhancedNewsFetcher.fetch_reddit_by_category(cat, limit_per_source)
                elif source == 'bbc':
                    arts = EnhancedNewsFetcher.fetch_bbc_rss(cat, limit_per_source)
                elif source in ['punch', 'vanguard', 'channels']:
                    arts = EnhancedNewsFetcher.fetch_nigerian_rss(source, cat, limit_per_source)
                else:
                    continue

                if arts:
                    all_articles.extend(arts)
                    print(f"✅ {len(arts)} articles")
                time.sleep(1)
        print(f"🎉 Total: {len(all_articles)}")
        return all_articles

    @staticmethod
    def generate_blog_post_from_article(article):
        """Convert article dict to Post object."""
        from django.utils.text import slugify
        from django.contrib.auth.models import User
        from blog.models import Category, Post
        from django.utils import timezone

        try:
            cat_name = article.get('category', 'NEWS')
            category_obj, _ = Category.objects.get_or_create(name=cat_name)
            author = User.objects.filter(username='admin').first() or User.objects.first()
            base_slug = slugify(article['title'][:50])
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            post = Post.objects.create(
                title=article['title'][:200],
                slug=slug,
                content=article.get('content', ''),
                excerpt=article.get('description', '')[:200],
                author=author,
                category=category_obj,
                published_date=timezone.now(),
            )
            post.tags.add('news', 'auto-generated', article.get('category', 'general').lower())
            if article.get('ai_processed'):
                post.tags.add('ai-rewritten')
            return post
        except Exception as e:
            print(f"❌ Post creation error: {e}")
            return None


# SimpleNewsFetcher kept for compatibility – now inherits from Enhanced
class SimpleNewsFetcher(EnhancedNewsFetcher):
    pass