# blog/ai_service.py - COMPLETE WITH GOOGLE GEMINI (500+ WORDS, BBC STYLE)
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
import re
from google import genai
from google.genai import types


class GeminiService:
    """Service for interacting with the new Google Gen AI SDK."""

    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY', ''))
        if not self.api_key:
            print("⚠️  No GEMINI_API_KEY found")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

    def generate_content(self, prompt, temperature=0.4, max_output_tokens=4096):
        """
        Send a prompt to Gemini (new SDK) and get response.
        Returns dict with 'success', 'content', 'word_count'.
        """
        if not self.client:
            return {'success': False, 'error': 'API key missing'}

        try:
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',  # Note: no '-latest' suffix
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                    top_p=0.95,
                    top_k=40
                )
            )
            text = response.text.strip()
            # Clean duplicate sentences (same as before)
            sentences = re.split(r'(?<=[.!?])\s+', text)
            seen = set()
            unique = []
            for s in sentences:
                norm = s.strip().lower()
                if norm and norm not in seen:
                    seen.add(norm)
                    unique.append(s)
            text = ' '.join(unique)
            word_count = len(text.split())
            return {'success': True, 'content': text, 'word_count': word_count}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def paraphrase_article(self, title, content, category, min_words=500):
        """Same as before, uses generate_content above."""
        prompt = f"""You are a senior journalist... (same prompt as before)"""
        result = self.generate_content(prompt, temperature=0.3, max_output_tokens=4096)
        if result['success'] and result['word_count'] < min_words:
            # Retry with stronger instruction
            prompt = f"""Your previous version was too short. You MUST write at least {min_words} words. 
Expand with more background, analysis, or details implied by the source, but do not invent facts.

Original title: {title}
Original content: {content[:8000]}

Write your expanded version now:"""
            result = self.generate_content(prompt, temperature=0.4, max_output_tokens=4096)
        return result



class EnhancedNewsFetcher:
    """Enhanced news fetcher with Google Gemini AI content generation"""

    SOURCES = {
        'google': {
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

    # === SCRAPING & GEMINI PROCESSING ===

    @staticmethod
    def scrape_article_content(url):
        """Scrape full article content from URL with improved error handling."""
        try:
            print(f"🔍 Scraping: {url[:70]}...")
            # Rotate user agents
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            ]
            import random
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            # Add small delay to avoid rate limits
            time.sleep(random.uniform(1, 2))
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()
            consent_markers = ['Before you continue', 'Accept all', 'Reject all', 'cookies and data', 'privacy settings']
            if any(marker in response.text for marker in consent_markers):
                print("❌ Consent page detected")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'form', 'button']):
                tag.decompose()

            content_selectors = [
                'article',
                '[class*="article-content"]',
                '[class*="article-body"]',
                '[class*="post-content"]',
                '[class*="entry-content"]',
                '[itemprop="articleBody"]',
                'div.content',
                'div.main-content',
                'div.post',
                '.story-body',
                '.story-content',
            ]

            content_area = None
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content_area = elements[0]
                    break

            if not content_area:
                content_area = soup.body

            if not content_area:
                return None

            paragraphs = content_area.find_all(['p', 'h2', 'h3', 'h4'])
            article_text = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 40:
                    article_text.append(text)

            full_text = '\n\n'.join(article_text)
            full_text = re.sub(r'\n\s*\n+', '\n\n', full_text)

            if len(full_text) < 200:
                print(f"⚠️  Content too short ({len(full_text)} chars)")
                return None

            if any(marker in full_text for marker in consent_markers):
                print("❌ Consent text in content")
                return None

            print(f"✅ Scraped {len(full_text)} characters")
            return full_text[:15000]

        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return None

    @staticmethod
    def rewrite_with_ai(title, content, source, category, min_words=500):
        """
        Use Google Gemini to rewrite content professionally.
        """
        gemini = GeminiService()
        if not gemini.configured:
            print("⚠️  Gemini not configured, cannot rewrite.")
            return None

        print(f"📝 Sending to Gemini for paraphrasing ({len(content)} chars)...")
        result = gemini.paraphrase_article(title, content, category, min_words)

        if result['success']:
            print(f"✅ Gemini generated {result['word_count']} words")
            summary = ' '.join(result['content'].split()[:200])
            return {
                'content': result['content'],
                'summary': summary,
                'word_count': result['word_count']
            }
        else:
            print(f"❌ Gemini error: {result.get('error')}")
            return None

    @staticmethod
    def process_article_with_ai(article_dict):
        """
        Process article: scrape content + Gemini rewrite to 500+ words.
        Returns None if scraping fails.
        """
        try:
            url = article_dict.get('url', '')
            title = article_dict.get('title', '')

            print(f"\n{'=' * 60}")
            print(f"📰 Processing: {title[:50]}...")
            print(f"URL: {url[:60]}...")

            scraped_content = EnhancedNewsFetcher.scrape_article_content(url)

            if not scraped_content or len(scraped_content) < 300:
                print("❌ Failed to scrape enough original content. Aborting.")
                return None

            ai_result = EnhancedNewsFetcher.rewrite_with_ai(
                title=title,
                content=scraped_content,
                source=article_dict.get('source', 'Unknown'),
                category=article_dict.get('category', 'NEWS'),
                min_words=500
            )

            if ai_result:
                article_dict['content'] = ai_result['content']
                article_dict['description'] = ai_result['summary']
                article_dict['word_count'] = ai_result['word_count']
                article_dict['ai_processed'] = True
                print(f"✅ SUCCESS: {ai_result['word_count']} words generated")
            else:
                # Fallback to scraped content
                print("⚠️  Gemini failed, using scraped content")
                article_dict['content'] = scraped_content[:5000]
                article_dict['description'] = scraped_content[:300]
                article_dict['word_count'] = len(scraped_content.split())
                article_dict['ai_processed'] = False

            print(f"{'=' * 60}\n")
            return article_dict

        except Exception as e:
            print(f"❌ Processing error: {e}")
            import traceback
            traceback.print_exc()
            return None

    # === NEWS FETCHING METHODS (unchanged from original) ===

    @staticmethod
    def fetch_news_api(category='general', country='nigeria', limit=10):
        """Fetch news from NewsAPI"""
        api_key = getattr(settings, 'NEWS_API_KEY', os.environ.get('NEWS_API_KEY', ''))

        if not api_key:
            print("⚠️  NewsAPI key not found")
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
            return []
        except Exception as e:
            print(f"❌ NewsAPI error: {e}")
            return []

    @staticmethod
    def fetch_google_news_by_category(category='news', limit=10, country='Nigeria'):
        """Fetch news from Google News"""
        try:
            source_key = 'google'
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
            print(f"❌ Google News error: {e}")
            return []

    @staticmethod
    def fetch_nigerian_rss(source, category='news', limit=10):
        """Fetch from Punch, Vanguard, Channels"""
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
            print(f"❌ {source} error: {e}")
            return []

    @staticmethod
    def fetch_reddit_by_category(category='news', limit=10):
        """Fetch from Reddit"""
        try:
            subreddit = EnhancedNewsFetcher.SOURCES['reddit']['subreddits'].get(category, 'news')
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
                        'published_at': datetime.fromtimestamp(post_data['created_utc']).isoformat(),
                        'source': f'Reddit r/{subreddit}',
                        'category': category.upper(),
                        'score': post_data['score'],
                        'comments': post_data['num_comments'],
                    })
                return news_items
            return []
        except Exception as e:
            print(f"❌ Reddit error: {e}")
            return []

    @staticmethod
    def fetch_bbc_rss(category='news', limit=10):
        """Fetch from BBC"""
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
            print(f"❌ BBC error: {e}")
            return []

    @staticmethod
    def fetch_multiple_sources(categories=None, sources=None, limit_per_source=5):
        """Fetch from multiple sources"""
        if categories is None:
            categories = ['news', 'sport', 'entertainment', 'economy', 'politics', 'technology']

        if sources is None:
            sources = ['google', 'reddit', 'bbc']

        all_articles = []

        for source in sources:
            for category in categories:
                print(f"📡 Fetching {category} from {source}...")

                if source == 'google':
                    articles = EnhancedNewsFetcher.fetch_google_news_by_category(category, limit_per_source)
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
                    all_articles.extend(articles)
                    print(f"✅ Found {len(articles)} articles from {source}/{category}")

                time.sleep(1)

        print(f"🎉 Total: {len(all_articles)} articles")
        return all_articles

    @staticmethod
    def generate_blog_post_from_article(article):
        """Generate blog post from article"""
        from django.utils.text import slugify
        from django.contrib.auth.models import User
        from blog.models import Category, Post

        try:
            category_name = article.get('category', 'NEWS')
            category_obj, created = Category.objects.get_or_create(name=category_name)

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

            content = article.get('content', '')

            post = Post.objects.create(
                title=article['title'][:200],
                slug=slug,
                content=content,
                excerpt=article.get('description', '')[:200] or article.get('title', '')[:200],
                author=author,
                category=category_obj,
                published_date=timezone.now(),
            )

            post.tags.add('news', 'auto-generated', article.get('category', 'general').lower())

            if article.get('ai_processed'):
                post.tags.add('ai-rewritten')

            print(f"✅ Created blog post: {post.title}")
            return post

        except Exception as e:
            print(f"❌ Error creating post: {e}")
            return None

    @staticmethod
    def extract_content_from_url(url):
        """Legacy method"""
        return EnhancedNewsFetcher.scrape_article_content(url)


# Backward compatibility
class SimpleNewsFetcher:
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