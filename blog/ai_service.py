# blog/ai_service.py - ENHANCED VERSION WITH NIGERIAN NEWS SOURCES
import os
import requests
import json
from datetime import datetime, timedelta
import feedparser
from django.conf import settings
from django.utils import timezone
import hashlib
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time


class EnhancedNewsFetcher:
    """Enhanced news fetcher with multiple sources and category support"""

    # News source configurations
    SOURCES = {
        'google': {
            'base_url': 'https://news.google.com/rss',
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
                'news': 'https://news.google.com/rss/search?q=Nigeria&hl=en-NG&gl=NG&ceid=NG:en',
                'sport': 'https://news.google.com/rss/search?q=Nigeria+sport&hl=en-NG&gl=NG&ceid=NG:en',
                'entertainment': 'https://news.google.com/rss/search?q=Nigeria+entertainment+nollywood&hl=en-NG&gl=NG&ceid=NG:en',
                'economy': 'https://news.google.com/rss/search?q=Nigeria+economy+business&hl=en-NG&gl=NG&ceid=NG:en',
                'politics': 'https://news.google.com/rss/search?q=Nigeria+politics&hl=en-NG&gl=NG&ceid=NG:en',
                'technology': 'https://news.google.com/rss/search?q=Nigeria+technology&hl=en-NG&gl=NG&ceid=NG:en',
            }
        },
        'nigerian_sources': {
            'punch': {
                'news': 'https://punchng.com/feed/',
                'sport': 'https://punchng.com/category/sports/feed/',
                'entertainment': 'https://punchng.com/category/entertainment/feed/',
                'economy': 'https://punchng.com/category/business/feed/',
                'politics': 'https://punchng.com/category/politics/feed/',
            },
            'vanguard': {
                'news': 'https://www.vanguardngr.com/feed/',
                'sport': 'https://www.vanguardngr.com/category/sports/feed/',
                'entertainment': 'https://www.vanguardngr.com/category/entertainment/feed/',
                'economy': 'https://www.vanguardngr.com/category/business/feed/',
                'politics': 'https://www.vanguardngr.com/category/politics/feed/',
            },
            'channels': {
                'news': 'https://www.channelstv.com/feed/',
                'politics': 'https://www.channelstv.com/category/politics/feed/',
                'economy': 'https://www.channelstv.com/category/business/feed/',
                'entertainment': 'https://www.channelstv.com/category/entertainment/feed/',
            },
            'thisday': {
                'news': 'https://www.thisdaylive.com/feed/',
                'economy': 'https://www.thisdaylive.com/category/business/feed/',
                'politics': 'https://www.thisdaylive.com/category/politics/feed/',
            },
            'guardian_ng': {
                'news': 'https://guardian.ng/feed/',
                'sport': 'https://guardian.ng/sport/feed/',
                'entertainment': 'https://guardian.ng/entertainment/feed/',
                'economy': 'https://guardian.ng/business-services/feed/',
                'politics': 'https://guardian.ng/politics/feed/',
            },
        },
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
        }
    }

    @staticmethod
    def fetch_news_api(category='general', country='us', limit=10):
        """Fetch news from NewsAPI"""
        api_key = getattr(settings, 'NEWS_API_KEY', os.environ.get('NEWS_API_KEY', ''))

        if not api_key:
            print("⚠️  NewsAPI key not found. Set NEWS_API_KEY in environment or settings.")
            return []

        try:
            url = f"https://newsapi.org/v2/top-headlines"
            params = {
                'apiKey': api_key,
                'category': category,
                'country': country,
                'pageSize': limit,
                'language': 'en'
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
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
                return articles
            else:
                print(f"❌ NewsAPI error: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"❌ Error fetching NewsAPI: {e}")
            return []

    @staticmethod
    def fetch_news_api_nigeria(category='general', limit=10):
        """Fetch Nigerian news from NewsAPI"""
        api_key = getattr(settings, 'NEWS_API_KEY', os.environ.get('NEWS_API_KEY', ''))

        if not api_key:
            print("⚠️  NewsAPI key not found.")
            return []

        try:
            # NewsAPI doesn't support country=ng for top-headlines directly
            # so we use the everything endpoint with Nigerian sources
            url = "https://newsapi.org/v2/everything"
            params = {
                'apiKey': api_key,
                'q': f'Nigeria {category}',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': limit,
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                articles = []

                for article in data.get('articles', []):
                    articles.append({
                        'title': article.get('title', 'Untitled'),
                        'description': article.get('description', ''),
                        'content': article.get('content', ''),
                        'url': article.get('url', ''),
                        'image_url': article.get('urlToImage', ''),
                        'published_at': article.get('publishedAt', ''),
                        'source': article.get('source', {}).get('name', 'NewsAPI Nigeria'),
                        'category': category.upper(),
                    })
                return articles
            else:
                print(f"❌ NewsAPI Nigeria error: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching NewsAPI Nigeria: {e}")
            return []

    @staticmethod
    def fetch_nigerian_rss(outlet='punch', category='news', limit=10):
        """Fetch news from Nigerian RSS feeds (Punch, Vanguard, Channels, etc.)"""
        try:
            outlet_sources = EnhancedNewsFetcher.SOURCES['nigerian_sources'].get(outlet, {})
            feed_url = outlet_sources.get(category) or outlet_sources.get('news')

            if not feed_url:
                print(f"⚠️ No RSS feed found for {outlet}/{category}")
                return []

            feed = feedparser.parse(feed_url)
            news_items = []

            outlet_names = {
                'punch': 'Punch Nigeria',
                'vanguard': 'Vanguard Nigeria',
                'channels': 'Channels TV',
                'thisday': 'ThisDay Live',
                'guardian_ng': 'Guardian Nigeria',
            }

            for entry in feed.entries[:limit]:
                news_items.append({
                    'title': entry.title,
                    'description': entry.get('summary', ''),
                    'content': entry.get('summary', ''),
                    'url': entry.link,
                    'published_at': entry.get('published', ''),
                    'source': outlet_names.get(outlet, outlet.title()),
                    'category': category.upper(),
                    'image_url': '',
                })
            return news_items
        except Exception as e:
            print(f"❌ Error fetching {outlet} RSS ({category}): {e}")
            return []

    @staticmethod
    def fetch_google_nigeria_news(category='news', limit=10):
        """Fetch Nigeria-specific news from Google News RSS"""
        try:
            category_url = EnhancedNewsFetcher.SOURCES['google_nigeria']['category_urls'].get(
                category,
                'https://news.google.com/rss/search?q=Nigeria&hl=en-NG&gl=NG&ceid=NG:en'
            )

            feed = feedparser.parse(category_url)
            news_items = []

            for entry in feed.entries[:limit]:
                news_items.append({
                    'title': entry.title,
                    'description': entry.get('summary', ''),
                    'content': entry.get('summary', ''),
                    'url': entry.link,
                    'published_at': entry.get('published', ''),
                    'source': entry.get('source', {}).get('title', 'Google News Nigeria'),
                    'category': category.upper(),
                })
            return news_items
        except Exception as e:
            print(f"❌ Error fetching Google Nigeria News ({category}): {e}")
            return []

    @staticmethod
    def fetch_google_news_by_category(category='news', limit=10):
        """Fetch news from Google News by specific category"""
        try:
            category_url = EnhancedNewsFetcher.SOURCES['google']['category_urls'].get(
                category,
                'https://news.google.com/rss'
            )

            feed = feedparser.parse(category_url)
            news_items = []

            for entry in feed.entries[:limit]:
                news_items.append({
                    'title': entry.title,
                    'description': entry.get('summary', ''),
                    'content': entry.get('summary', ''),
                    'url': entry.link,
                    'published_at': entry.get('published', ''),
                    'source': entry.get('source', {}).get('title', 'Google News'),
                    'category': category.upper(),
                })
            return news_items
        except Exception as e:
            print(f"❌ Error fetching Google News ({category}): {e}")
            return []

    @staticmethod
    def fetch_reddit_by_category(category='news', limit=10):
        """Fetch news from Reddit by category/subreddit"""
        try:
            subreddit = EnhancedNewsFetcher.SOURCES['reddit']['subreddits'].get(
                category, 'news'
            )

            url = f'https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}'
            headers = {'User-agent': 'newsbot/1.0'}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                news_items = []

                for post in data['data']['children']:
                    post_data = post['data']
                    news_items.append({
                        'title': post_data['title'],
                        'description': post_data.get('selftext', '')[:200],
                        'content': post_data.get('selftext', ''),
                        'url': f"https://reddit.com{post_data['permalink']}",
                        'published_at': datetime.fromtimestamp(
                            post_data['created_utc']
                        ).isoformat(),
                        'source': f'Reddit r/{subreddit}',
                        'category': category.upper(),
                        'score': post_data['score'],
                        'comments': post_data['num_comments'],
                    })
                return news_items
            else:
                print(f"❌ Reddit error: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching Reddit ({category}): {e}")
            return []

    @staticmethod
    def fetch_bbc_rss(category='news', limit=10):
        """Fetch news from BBC RSS feeds"""
        try:
            feed_url = EnhancedNewsFetcher.SOURCES['bbc']['category_urls'].get(
                category, 'http://feeds.bbci.co.uk/news/rss.xml'
            )

            feed = feedparser.parse(feed_url)
            news_items = []

            for entry in feed.entries[:limit]:
                news_items.append({
                    'title': entry.title,
                    'description': entry.get('summary', ''),
                    'content': entry.get('summary', ''),
                    'url': entry.link,
                    'published_at': entry.get('published', ''),
                    'source': 'BBC News',
                    'category': category.upper(),
                })
            return news_items
        except Exception as e:
            print(f"❌ Error fetching BBC RSS ({category}): {e}")
            return []

    @staticmethod
    def fetch_multiple_sources(categories=None, sources=None, limit_per_source=5):
        """Fetch news from multiple sources including Nigerian outlets"""
        if categories is None:
            categories = ['news', 'sport', 'entertainment', 'economy', 'politics', 'technology']

        if sources is None:
            sources = ['google', 'google_nigeria', 'punch', 'vanguard', 'channels', 'bbc', 'reddit']

        all_articles = []

        nigerian_outlets = ['punch', 'vanguard', 'channels', 'thisday', 'guardian_ng']

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
                    articles = EnhancedNewsFetcher.fetch_news_api(
                        EnhancedNewsFetcher.SOURCES['newsapi']['categories'].get(category, 'general'),
                        limit=limit_per_source
                    )
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
                    print(f"✅ Found {len(articles)} articles from {source}/{category}")

                # Avoid rate limiting
                time.sleep(1)

        print(f"🎉 Total articles fetched: {len(all_articles)}")
        return all_articles

    @staticmethod
    def generate_blog_post_from_article(article):
        """Generate a blog post from a news article"""
        from django.utils.text import slugify
        from django.contrib.auth.models import User
        from blog.models import Category, Post
        from django.utils import timezone

        try:
            category_name = article.get('category', 'NEWS')
            category_obj, created = Category.objects.get_or_create(
                name=category_name
            )

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

            enhanced_content = f"""
            <h1>{article['title']}</h1>
            <div class="alert alert-info">
                <strong>Source:</strong> {article.get('source', 'Unknown')}<br>
                <strong>Published:</strong> {article.get('published_at', 'N/A')}<br>
                <strong>Original URL:</strong> <a href="{article['url']}" target="_blank">{article['url'][:100]}...</a>
            </div>
            <hr>
            """

            if article.get('description'):
                enhanced_content += f"<p><strong>Summary:</strong> {article['description']}</p>"

            if article.get('content'):
                enhanced_content += f"\n<div class='article-content'>{article['content'][:2000]}"
                if len(article.get('content', '')) > 2000:
                    enhanced_content += "... [Content truncated]"
                enhanced_content += "</div>"

            enhanced_content += f"""
            <hr>
            <div class="alert alert-secondary">
                <em>This article was automatically generated from {article.get('source', 'a news source')}.
                <a href="{article.get('url', '#')}" target="_blank" class="btn btn-sm btn-outline-primary">
                    Read original article
                </a></em>
            </div>
            """

            post = Post.objects.create(
                title=f"[News] {article['title'][:100]}",
                slug=slug,
                content=enhanced_content,
                excerpt=article.get('description', '')[:200] or article.get('title', '')[:200],
                author=author,
                category=category_obj,
                published_date=timezone.now(),
            )

            post.tags.add('news', 'auto-generated', article.get('category', 'general').lower())

            print(f"✅ Created blog post: {post.title}")
            return post

        except Exception as e:
            print(f"❌ Error generating blog post: {e}")
            return None

    @staticmethod
    def extract_content_from_url(url):
        """Extract main content from URL"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text[:5000]
        except Exception as e:
            print(f"❌ Error extracting content: {e}")
            return None


# Keep the original SimpleNewsFetcher for backward compatibility
class SimpleNewsFetcher:
    """Original simple news fetcher (for backward compatibility)"""

    @staticmethod
    def fetch_google_news_rss():
        # Fetch both international and Nigerian news
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
            'ENTERTAINMENT': ['movie', 'film', 'actor', 'actress', 'celebrity', 'music', 'show', 'tv', 'hollywood', 'nollywood', 'afrobeats'],
            'SPORT': ['sport', 'football', 'basketball', 'soccer', 'game', 'team', 'player', 'score', 'win', 'super eagles', 'afcon', 'laliga', 'premier league'],
            'POLITICS': ['government', 'president', 'minister', 'election', 'vote', 'party', 'congress', 'senate', 'tinubu', 'nigeria politics', 'abuja', 'aso rock'],
            'ECONOMY': ['economy', 'market', 'stock', 'price', 'bank', 'money', 'business', 'company', 'dollar', 'naira', 'cbn', 'inflation', 'oil'],
            'NEWS': ['news', 'report', 'announce', 'official', 'statement', 'update', 'latest'],
            'VIRAL GIST': ['viral', 'trending', 'social media', 'tiktok', 'instagram', 'twitter', 'facebook'],
        }

        scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[category] = score

        best_category = max(scores, key=scores.get)

        if scores[best_category] < 2:
            return 'NEWS'

        return best_category

    @staticmethod
    def generate_summary(text, max_length=150):
        if not text:
            return ""

        if len(text) <= max_length:
            return text

        sentences = text.split('. ')
        if len(sentences) <= 3:
            return text[:max_length] + '...'

        summary = sentences[0]
        if len(sentences) > 1:
            summary += '. ' + sentences[-1]

        if len(summary) > max_length:
            summary = summary[:max_length] + '...'

        return summary

    @staticmethod
    def extract_content_from_url(url):
        return EnhancedNewsFetcher.extract_content_from_url(url)