# blog/ai_service.py - FINAL VERSION (NO GOOGLE NEWS, BETTER DEBUGGING)
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

    @staticmethod
    def scrape_full_article_content(url):
        """Scrape article content – returns None if consent page detected."""
        # ... keep your existing scraping code (same as before)
        # For brevity, I'm not repeating it here. Keep your current method.
        pass

    @staticmethod
    def summarize_and_rewrite_with_ai(article_title, article_content, source, category, min_words=500):
        # Keep your existing AI method (unchanged)
        pass

    @staticmethod
    def process_article_with_ai(article_dict):
        # Keep your existing processing method (unchanged)
        pass

    # ===== FETCH METHODS =====

    @staticmethod
    def fetch_news_api(category='general', country='ng', limit=10):
        """Fetch from NewsAPI with detailed logging and fallback to 'us'."""
        api_key = getattr(settings, 'NEWS_API_KEY', os.environ.get('NEWS_API_KEY', ''))
        if not api_key:
            print("❌ NEWS_API_KEY not found in environment or settings!")
            return []

        print(f"📡 NewsAPI: fetching {category} for {country} (limit {limit})...")

        url = "https://newsapi.org/v2/top-headlines"
        params = {
            'apiKey': api_key,
            'category': category,
            'country': country,
            'pageSize': limit,
            'language': 'en'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"   NewsAPI response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"   NewsAPI status: {data.get('status')}, totalResults: {data.get('totalResults', 0)}")

                if data.get('status') != 'ok':
                    print(f"   NewsAPI error message: {data.get('message', 'Unknown error')}")
                    return []

                articles = []
                for article in data.get('articles', []):
                    articles.append({
                        'title': article.get('title', 'Untitled'),
                        'description': article.get('description', ''),
                        'content': article.get('content', ''),
                        'url': article.get('url', ''),
                        'image_url': article.get('urlToImage', ''),
                        'published_at': article.get('publishedAt', ''),
                        'source': article.get('source', {}).get('name', 'NewsAPI'),
                        'category': category.upper(),
                    })

                # If no articles for Nigeria, try US as fallback
                if not articles and country == 'ng':
                    print("⚠️  No articles for Nigeria, falling back to US...")
                    return EnhancedNewsFetcher.fetch_news_api(category, 'us', limit)

                return articles
            else:
                print(f"❌ NewsAPI HTTP error {response.status_code}: {response.text[:200]}")
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
                    print(f"✅ {len(arts)} articles from {source}/{cat}")
                else:
                    print(f"⚠️  No articles from {source}/{cat}")
                time.sleep(1)
        print(f"🎉 Total articles fetched: {len(all_articles)}")
        return all_articles

    @staticmethod
    def generate_blog_post_from_article(article):
        """Generate a blog post from a news article."""
        # Keep your existing method (unchanged)
        pass


# SimpleNewsFetcher for backward compatibility – now inherits from Enhanced
class SimpleNewsFetcher(EnhancedNewsFetcher):
    pass