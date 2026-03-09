# blog/ai_service.py - FIXED VERSION WITH WORKING NIGERIAN NEWS
import os
import requests
import json
from datetime import datetime, timedelta
import feedparser
from django.conf import settings
from django.utils import timezone
import hashlib
from urllib.parse import urlparse, quote
from bs4 import BeautifulSoup
import time


class EnhancedNewsFetcher:
    """Enhanced news fetcher with multiple sources including Nigerian outlets"""

    SOURCES = {
        'google': {
            'category_urls': {
                'news': 'https://news.google.com/rss',
                'sport': 'https://news.google.com/rss/headlines/section/topic/SPORT',
                'entertainment': 'https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT',
                'economy': 'https://news.google.com/rss/headlines/section/topic/BUSINESS',
                'politics': 'https://news.google.com/rss/headlines/section/topic/POLITICS',
                'technology': 'https://news.google.com/rss/headlines/section/topic/TECHNOLOGY',
            }
        },
        'google_nigeria': {
            'category_urls': {
                'news':          'https://news.google.com/rss/search?q=Nigeria+news&hl=en-NG&gl=NG&ceid=NG:en',
                'sport':         'https://news.google.com/rss/search?q=Nigeria+sport+football&hl=en-NG&gl=NG&ceid=NG:en',
                'entertainment': 'https://news.google.com/rss/search?q=Nigeria+entertainment+nollywood&hl=en-NG&gl=NG&ceid=NG:en',
                'economy':       'https://news.google.com/rss/search?q=Nigeria+economy+naira+CBN&hl=en-NG&gl=NG&ceid=NG:en',
                'politics':      'https://news.google.com/rss/search?q=Nigeria+politics+government&hl=en-NG&gl=NG&ceid=NG:en',
                'technology':    'https://news.google.com/rss/search?q=Nigeria+technology+tech&hl=en-NG&gl=NG&ceid=NG:en',
            }
        },
        'nigerian_sources': {
            'punch': {
                'news':          'https://punchng.com/feed/',
                'sport':         'https://punchng.com/category/sports/feed/',
                'entertainment': 'https://punchng.com/category/entertainment/feed/',
                'economy':       'https://punchng.com/category/business/feed/',
                'politics':      'https://punchng.com/category/politics/feed/',
            },
            'vanguard': {
                'news':          'https://www.vanguardngr.com/feed/',
                'sport':         'https://www.vanguardngr.com/category/sports/feed/',
                'entertainment': 'https://www.vanguardngr.com/category/entertainment/feed/',
                'economy':       'https://www.vanguardngr.com/category/business/feed/',
                'politics':      'https://www.vanguardngr.com/category/politics/feed/',
            },
            'channels': {
                'news':          'https://www.channelstv.com/feed/',
                'politics':      'https://www.channelstv.com/category/politics/feed/',
                'economy':       'https://www.channelstv.com/category/business/feed/',
                'entertainment': 'https://www.channelstv.com/category/entertainment/feed/',
                'sport':         'https://www.channelstv.com/category/sports/feed/',
            },
            'thisday': {
                'news':          'https://www.thisdaylive.com/feed/',
                'economy':       'https://www.thisdaylive.com/category/business/feed/',
                'politics':      'https://www.thisdaylive.com/category/politics/feed/',
                'sport':         'https://www.thisdaylive.com/category/sports/feed/',
            },
            'guardian_ng': {
                'news':          'https://guardian.ng/feed/',
                'sport':         'https://guardian.ng/sport/feed/',
                'entertainment': 'https://guardian.ng/entertainment/feed/',
                'economy':       'https://guardian.ng/business-services/feed/',
                'politics':      'https://guardian.ng/politics/feed/',
            },
        },
        'reddit': {
            'subreddits': {
                'news': 'news', 'sport': 'sports', 'entertainment': 'entertainment',
                'economy': 'economy', 'politics': 'politics', 'technology': 'technology',
            }
        },
        'bbc': {
            'category_urls': {
                'news':          'http://feeds.bbci.co.uk/news/rss.xml',
                'sport':         'http://feeds.bbci.co.uk/sport/rss.xml',
                'entertainment': 'http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml',
                'economy':       'http://feeds.bbci.co.uk/news/business/rss.xml',
                'technology':    'http://feeds.bbci.co.uk/news/technology/rss.xml',
                'politics':      'http://feeds.bbci.co.uk/news/politics/rss.xml',
            }
        }
    }

    # Browser-like headers to avoid RSS blocks
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
    }

    @staticmethod
    def fetch_rss_feed(url, source_name, category, limit=10):
        """Generic RSS fetcher with browser headers to avoid blocks"""
        try:
            response = requests.get(url, headers=EnhancedNewsFetcher.HEADERS, timeout=15)
            if response.status_code != 200:
                print(f"⚠️ {source_name} returned {response.status_code}")
                return []

            feed = feedparser.parse(response.content)

            if not feed.entries:
                print(f"⚠️ {source_name} feed empty for {url}")
                return []

            items = []
            for entry in feed.entries[:limit]:
                image_url = ''
                if hasattr(entry, 'media_content') and entry.media_content:
                    image_url = entry.media_content[0].get('url', '')
                elif hasattr(entry, 'enclosures') and entry.enclosures:
                    image_url = entry.enclosures[0].get('href', '')

                items.append({
                    'title': entry.get('title', 'Untitled'),
                    'description': entry.get('summary', ''),
                    'content': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'published_at': entry.get('published', ''),
                    'source': source_name,
                    'category': category.upper(),
                    'image_url': image_url,
                })
            print(f"✅ {source_name}: {len(items)} articles")
            return items

        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout: {source_name}")
            return []
        except Exception as e:
            print(f"❌ {source_name} error: {e}")
            return []

    @staticmethod
    def fetch_news_api(category='general', country='us', limit=10):
        """Fetch from NewsAPI"""
        api_key = getattr(settings, 'NEWS_API_KEY', os.environ.get('NEWS_API_KEY', ''))
        if not api_key:
            print("⚠️ NewsAPI key not found.")
            return []
        try:
            params = {'apiKey': api_key, 'category': category, 'country': country, 'pageSize': limit, 'language': 'en'}
            r = requests.get("https://newsapi.org/v2/top-headlines", params=params, timeout=10)
            if r.status_code == 200:
                return [{
                    'title': a.get('title', 'Untitled'),
                    'description': a.get('description', ''),
                    'content': a.get('content', ''),
                    'url': a.get('url', ''),
                    'image_url': a.get('urlToImage', ''),
                    'published_at': a.get('publishedAt', ''),
                    'source': a.get('source', {}).get('name', 'NewsAPI'),
                    'category': category.upper(),
                } for a in r.json().get('articles', [])]
            return []
        except Exception as e:
            print(f"❌ NewsAPI error: {e}")
            return []

    @staticmethod
    def fetch_news_api_nigeria(category='general', limit=10):
        """Fetch Nigerian news from NewsAPI"""
        api_key = getattr(settings, 'NEWS_API_KEY', os.environ.get('NEWS_API_KEY', ''))
        if not api_key:
            return []
        try:
            params = {'apiKey': api_key, 'q': f'Nigeria {category}', 'language': 'en', 'sortBy': 'publishedAt', 'pageSize': limit}
            r = requests.get("https://newsapi.org/v2/everything", params=params, timeout=10)
            if r.status_code == 200:
                return [{
                    'title': a.get('title', 'Untitled'),
                    'description': a.get('description', ''),
                    'content': a.get('content', ''),
                    'url': a.get('url', ''),
                    'image_url': a.get('urlToImage', ''),
                    'published_at': a.get('publishedAt', ''),
                    'source': a.get('source', {}).get('name', 'NewsAPI Nigeria'),
                    'category': category.upper(),
                } for a in r.json().get('articles', [])]
            return []
        except Exception as e:
            print(f"❌ NewsAPI Nigeria error: {e}")
            return []

    @staticmethod
    def fetch_google_nigeria_news(category='news', limit=10):
        """Fetch Nigeria-filtered news from Google News RSS"""
        url = EnhancedNewsFetcher.SOURCES['google_nigeria']['category_urls'].get(
            category,
            'https://news.google.com/rss/search?q=Nigeria+news&hl=en-NG&gl=NG&ceid=NG:en'
        )
        return EnhancedNewsFetcher.fetch_rss_feed(url, 'Google News Nigeria', category, limit)

    @staticmethod
    def fetch_nigerian_rss(outlet='punch', category='news', limit=10):
        """Fetch from Nigerian RSS outlets"""
        outlet_names = {
            'punch': 'Punch Nigeria', 'vanguard': 'Vanguard Nigeria',
            'channels': 'Channels TV', 'thisday': 'ThisDay Live', 'guardian_ng': 'Guardian Nigeria',
        }
        sources = EnhancedNewsFetcher.SOURCES['nigerian_sources'].get(outlet, {})
        url = sources.get(category) or sources.get('news')
        if not url:
            return []
        return EnhancedNewsFetcher.fetch_rss_feed(url, outlet_names.get(outlet, outlet), category, limit)

    @staticmethod
    def fetch_google_news_by_category(category='news', limit=10):
        url = EnhancedNewsFetcher.SOURCES['google']['category_urls'].get(category, 'https://news.google.com/rss')
        return EnhancedNewsFetcher.fetch_rss_feed(url, 'Google News', category, limit)

    @staticmethod
    def fetch_reddit_by_category(category='news', limit=10):
        subreddit = EnhancedNewsFetcher.SOURCES['reddit']['subreddits'].get(category, 'news')
        try:
            r = requests.get(f'https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}', headers={'User-agent': 'newsbot/1.0'}, timeout=10)
            if r.status_code == 200:
                return [{
                    'title': p['data']['title'],
                    'description': p['data'].get('selftext', '')[:200],
                    'content': p['data'].get('selftext', ''),
                    'url': f"https://reddit.com{p['data']['permalink']}",
                    'published_at': datetime.fromtimestamp(p['data']['created_utc']).isoformat(),
                    'source': f'Reddit r/{subreddit}',
                    'category': category.upper(),
                    'image_url': '',
                } for p in r.json()['data']['children']]
            return []
        except Exception as e:
            print(f"❌ Reddit error: {e}")
            return []

    @staticmethod
    def fetch_bbc_rss(category='news', limit=10):
        url = EnhancedNewsFetcher.SOURCES['bbc']['category_urls'].get(category, 'http://feeds.bbci.co.uk/news/rss.xml')
        return EnhancedNewsFetcher.fetch_rss_feed(url, 'BBC News', category, limit)

    @staticmethod
    def fetch_multiple_sources(categories=None, sources=None, limit_per_source=5):
        if categories is None:
            categories = ['news', 'sport', 'entertainment', 'economy', 'politics', 'technology']
        if sources is None:
            sources = ['google', 'google_nigeria', 'punch', 'vanguard', 'bbc']

        nigerian_outlets = ['punch', 'vanguard', 'channels', 'thisday', 'guardian_ng']
        all_articles = []

        for source in sources:
            for category in categories:
                print(f"📡 Fetching {category} from {source}...")
                if source == 'google':
                    articles = EnhancedNewsFetcher.fetch_google_news_by_category(category, limit_per_source)
                elif source == 'google_nigeria':
                    articles = EnhancedNewsFetcher.fetch_google_nigeria_news(category, limit_per_source)
                elif source in nigerian_outlets:
                    articles = EnhancedNewsFetcher.fetch_nigerian_rss(source, category, limit_per_source)
                elif source == 'newsapi':
                    cat_map = {'news': 'general', 'sport': 'sports', 'entertainment': 'entertainment', 'economy': 'business', 'politics': 'general', 'technology': 'technology'}
                    articles = EnhancedNewsFetcher.fetch_news_api(cat_map.get(category, 'general'), limit=limit_per_source)
                elif source == 'newsapi_nigeria':
                    articles = EnhancedNewsFetcher.fetch_news_api_nigeria(category, limit_per_source)
                elif source == 'reddit':
                    articles = EnhancedNewsFetcher.fetch_reddit_by_category(category, limit_per_source)
                elif source == 'bbc':
                    articles = EnhancedNewsFetcher.fetch_bbc_rss(category, limit_per_source)
                else:
                    continue

                if articles:
                    all_articles.extend(articles)
                time.sleep(0.5)

        print(f"🎉 Total: {len(all_articles)} articles")
        return all_articles

    @staticmethod
    def generate_blog_post_from_article(article):
        from django.utils.text import slugify
        from django.contrib.auth.models import User
        from blog.models import Category, Post

        try:
            category_obj, _ = Category.objects.get_or_create(name=article.get('category', 'NEWS'))
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

            content = f"""
            <h1>{article['title']}</h1>
            <div class="alert alert-info">
                <strong>Source:</strong> {article.get('source', 'Unknown')}<br>
                <strong>Original:</strong> <a href="{article['url']}" target="_blank">Read full article</a>
            </div>
            <hr>
            <p>{article.get('description', '')}</p>
            <div>{article.get('content', '')[:2000]}</div>
            <hr>
            <div class="alert alert-secondary">
                <em>Auto-generated from {article.get('source', 'a news source')}.
                <a href="{article.get('url','#')}" target="_blank" class="btn btn-sm btn-outline-primary">Read original</a></em>
            </div>
            """

            post = Post.objects.create(
                title=f"[News] {article['title'][:100]}",
                slug=slug,
                content=content,
                excerpt=article.get('description', '')[:200] or article.get('title', '')[:200],
                author=author,
                category=category_obj,
                published_date=timezone.now(),
            )
            post.tags.add('news', 'auto-generated', article.get('category', 'general').lower())
            print(f"✅ Created post: {post.title}")
            return post
        except Exception as e:
            print(f"❌ Error generating post: {e}")
            return None

    @staticmethod
    def extract_content_from_url(url):
        try:
            r = requests.get(url, headers=EnhancedNewsFetcher.HEADERS, timeout=10)
            soup = BeautifulSoup(r.content, 'html.parser')
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            return ' '.join(soup.get_text().split())[:5000]
        except Exception as e:
            print(f"❌ Content extract error: {e}")
            return None


class SimpleNewsFetcher:
    """Backward-compatible fetcher"""

    @staticmethod
    def fetch_google_news_rss():
        international = EnhancedNewsFetcher.fetch_google_news_by_category('news', 8)
        nigerian = EnhancedNewsFetcher.fetch_google_nigeria_news('news', 8)
        punch = EnhancedNewsFetcher.fetch_nigerian_rss('punch', 'news', 5)
        vanguard = EnhancedNewsFetcher.fetch_nigerian_rss('vanguard', 'news', 5)
        return international + nigerian + punch + vanguard

    @staticmethod
    def fetch_reddit_news(subreddit='news', limit=10):
        return EnhancedNewsFetcher.fetch_reddit_by_category('news', limit)

    @staticmethod
    def fetch_newsapi():
        international = EnhancedNewsFetcher.fetch_news_api('general', 'us', 5)
        nigerian = EnhancedNewsFetcher.fetch_news_api_nigeria('general', 5)
        return international + nigerian

    @staticmethod
    def categorize_article(title, description):
        text = (title + ' ' + description).lower()
        categories = {
            'ENTERTAINMENT': ['movie', 'film', 'actor', 'actress', 'celebrity', 'music', 'show', 'tv', 'hollywood', 'nollywood', 'afrobeats', 'wizkid', 'davido', 'burna'],
            'SPORT': ['sport', 'football', 'basketball', 'soccer', 'game', 'team', 'player', 'score', 'win', 'super eagles', 'afcon', 'laliga', 'premier league', 'npfl'],
            'POLITICS': ['government', 'president', 'minister', 'election', 'vote', 'party', 'congress', 'senate', 'tinubu', 'abuja', 'aso rock', 'national assembly', 'governor'],
            'ECONOMY': ['economy', 'market', 'stock', 'price', 'bank', 'money', 'business', 'company', 'dollar', 'naira', 'cbn', 'inflation', 'oil', 'forex', 'budget'],
            'TECHNOLOGY': ['technology', 'tech', 'software', 'app', 'digital', 'startup', 'fintech', 'ai', 'internet'],
            'NEWS': ['news', 'report', 'announce', 'official', 'statement', 'update', 'latest'],
            'VIRAL GIST': ['viral', 'trending', 'social media', 'tiktok', 'instagram', 'twitter', 'facebook'],
        }
        scores = {cat: sum(1 for kw in kws if kw in text) for cat, kws in categories.items()}
        best = max(scores, key=scores.get)
        return best if scores[best] >= 2 else 'NEWS'

    @staticmethod
    def generate_summary(text, max_length=150):
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        sentences = text.split('. ')
        summary = sentences[0]
        if len(sentences) > 1:
            summary += '. ' + sentences[-1]
        return summary[:max_length] + '...' if len(summary) > max_length else summary

    @staticmethod
    def extract_content_from_url(url):
        return EnhancedNewsFetcher.extract_content_from_url(url)