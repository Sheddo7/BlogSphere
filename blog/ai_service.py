# blog/ai_service.py - ENHANCED VERSION WITH NIGERIAN NEWS SUPPORT
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

        'google_nigeria': {
            'base_url': 'https://news.google.com/rss?hl=en-NG&gl=NG&ceid=NG:en',
            'category_urls': {
                'news': 'https://news.google.com/rss?hl=en-NG&gl=NG&ceid=NG:en',
                'sport': 'https://news.google.com/rss/headlines/section/topic/SPORTS?hl=en-NG&gl=NG&ceid=NG:en',
                'entertainment': 'https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-NG&gl=NG&ceid=NG:en',
                'economy': 'https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-NG&gl=NG&ceid=NG:en',
                'politics': 'https://news.google.com/rss/headlines/section/topic/POLITICS?hl=en-NG&gl=NG&ceid=NG:en',
                'technology': 'https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-NG&gl=NG&ceid=NG:en',
            }
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
    def fetch_news_api(category='general', country='nigeria', limit=10):
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
    def fetch_google_news_by_category(category='news', limit=10, country='Nigeria'):
        """Fetch news from Google News by specific category

        Args:
            category: news category (news, sport, entertainment, etc.)
            limit: number of articles to fetch
            country: if 'nigeria', fetches from Nigerian Google News
        """
        try:
            # Choose source based on country parameter
            source_key = 'google_nigeria' if country == 'nigeria' else 'google'

            # Get the category URL or default to general news
            category_url = EnhancedNewsFetcher.SOURCES[source_key]['category_urls'].get(
                category,
                EnhancedNewsFetcher.SOURCES[source_key]['base_url']
            )

            feed = feedparser.parse(category_url)
            news_items = []

            for entry in feed.entries[:limit]:
                source_name = entry.get('source', {}).get('title', 'Google News')
                if country == 'nigeria':
                    source_name = f"{source_name} (Nigeria)"

                news_items.append({
                    'title': entry.title,
                    'description': entry.get('summary', ''),
                    'content': entry.get('summary', ''),
                    'url': entry.link,
                    'published_at': entry.get('published', ''),
                    'source': source_name,
                    'category': category.upper(),
                })
            return news_items
        except Exception as e:
            print(f"❌ Error fetching Google News ({category}, {country}): {e}")
            return []

    @staticmethod
    def fetch_nigerian_rss(source, category='news', limit=10):
        """Fetch news from Nigerian news sources (Punch, Vanguard, Channels)"""
        try:
            if source not in ['punch', 'vanguard', 'channels']:
                return []

            feed_url = EnhancedNewsFetcher.SOURCES[source]['category_urls'].get(
                category,
                EnhancedNewsFetcher.SOURCES[source].get('base_url', '')
            )

            if not feed_url:
                return []

            feed = feedparser.parse(feed_url)
            news_items = []

            for entry in feed.entries[:limit]:
                news_items.append({
                    'title': entry.title,
                    'description': entry.get('summary', ''),
                    'content': entry.get('summary', ''),
                    'url': entry.link,
                    'published_at': entry.get('published', ''),
                    'source': source.capitalize(),
                    'category': category.upper(),
                })
            return news_items
        except Exception as e:
            print(f"❌ Error fetching {source} ({category}): {e}")
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
                    'source': 'BBC',
                    'category': category.upper(),
                })
            return news_items
        except Exception as e:
            print(f"❌ Error fetching BBC ({category}): {e}")
            return []

    @staticmethod
    def fetch_multiple_sources(categories=None, sources=None, limit_per_source=5):
        """Fetch news from multiple sources and categories

        NOW SUPPORTS: google_nigeria, punch, vanguard, channels sources
        """
        if categories is None:
            categories = ['news', 'sport', 'entertainment', 'economy', 'politics', 'technology']

        if sources is None:
            sources = ['google', 'reddit', 'bbc']

        all_articles = []

        for source in sources:
            for category in categories:
                print(f"📡 Fetching {category} from {source}...")

                if source == 'google':
                    # Fetch BOTH international AND Nigerian Google News
                    # International first
                    articles = EnhancedNewsFetcher.fetch_google_news_by_category(
                        category,
                        limit=limit_per_source // 2  # Split limit between international and Nigerian
                    )
                    if articles:
                        all_articles.extend(articles)

                    # Then Nigerian
                    ng_articles = EnhancedNewsFetcher.fetch_google_news_by_category(
                        category,
                        limit=limit_per_source // 2,
                        country='nigeria'
                    )
                    if ng_articles:
                        all_articles.extend(ng_articles)
                        articles = articles + ng_articles  # For count

                elif source == 'google_nigeria':
                    articles = EnhancedNewsFetcher.fetch_google_news_by_category(
                        category,
                        limit=limit_per_source,
                        country='nigeria'
                    )
                elif source == 'reddit':
                    articles = EnhancedNewsFetcher.fetch_reddit_by_category(category, limit_per_source)
                elif source == 'newsapi':
                    articles = EnhancedNewsFetcher.fetch_news_api(
                        EnhancedNewsFetcher.SOURCES['newsapi']['categories'].get(category, 'general'),
                        limit=limit_per_source
                    )
                elif source == 'bbc':
                    articles = EnhancedNewsFetcher.fetch_bbc_rss(category, limit_per_source)
                elif source in ['punch', 'vanguard', 'channels']:
                    articles = EnhancedNewsFetcher.fetch_nigerian_rss(source, category, limit_per_source)
                else:
                    continue

                if articles:
                    # Only extend if we haven't already (google case handles it above)
                    if source != 'google':
                        all_articles.extend(articles)
                    print(f"✅ Found {len(articles)} articles from {source}/{category}")

                # Avoid rate limiting
                time.sleep(1)

        print(f"🎉 Total articles fetched: {len(all_articles)}")
        return all_articles

    # Keep all other methods unchanged from your original file
    # (generate_blog_post_from_article, scrape_article, etc.)
    def generate_blog_post_from_article(article):
        """Generate a blog post from a news article"""
        from django.utils.text import slugify
        from django.contrib.auth.models import User
        from blog.models import Category, Post
        from django.utils import timezone

        try:
            # Get or create category
            category_name = article.get('category', 'NEWS')
            category_obj, created = Category.objects.get_or_create(
                name=category_name
            )

            # Get admin user
            try:
                author = User.objects.get(username='admin')
            except User.DoesNotExist:
                author = User.objects.first()

            # Generate slug
            base_slug = slugify(article['title'][:50])
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Enhance content
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

            # Create blog post
            post = Post.objects.create(
                title=f"[News] {article['title'][:100]}",
                slug=slug,
                content=enhanced_content,
                excerpt=article.get('description', '')[:200] or article.get('title', '')[:200],
                author=author,
                category=category_obj,
                published_date=timezone.now(),
            )

            # Add tags
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

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up text
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
        return EnhancedNewsFetcher.fetch_google_news_by_category('news', 15)

    @staticmethod
    def fetch_reddit_news(subreddit='news', limit=10):
        return EnhancedNewsFetcher.fetch_reddit_by_category('news', limit)

    @staticmethod
    def categorize_article(title, description):
        text = (title + ' ' + description).lower()

        categories = {
            'ENTERTAINMENT': ['movie', 'film', 'actor', 'actress', 'celebrity', 'music', 'show', 'tv', 'hollywood'],
            'SPORT': ['sport', 'football', 'basketball', 'soccer', 'game', 'team', 'player', 'score', 'win'],
            'POLITICS': ['government', 'president', 'minister', 'election', 'vote', 'party', 'congress', 'senate'],
            'ECONOMY': ['economy', 'market', 'stock', 'price', 'bank', 'money', 'business', 'company', 'dollar'],
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