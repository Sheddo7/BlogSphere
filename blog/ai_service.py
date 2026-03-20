# blog/ai_service.py - COMPLETE WITH OPENROUTER (NO SOURCE ATTRIBUTION)
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
import random

def format_content(text):
    if not text:
        return ''
    if '<p>' in text or '<div>' in text or '<h2>' in text:
        return text
    import re
    paragraphs = re.split(r'\n\n+|\n', text)
    formatted = ''
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) < 80 and not para.endswith(('.', ',', '?', '!')):
            formatted += f'<h3>{para}</h3>\n'
        else:
            formatted += f'<p>{para}</p>\n'
    return formatted


class OpenRouterService:
    """Service for interacting with OpenRouter API (free tier, 50-1000 requests/day)"""

    def __init__(self):
        self.api_key = getattr(settings, 'OPENROUTER_API_KEY', os.environ.get('OPENROUTER_API_KEY', ''))
        if not self.api_key:
            print("⚠️  No OPENROUTER_API_KEY found")
            self.api_key = None
        else:
            self.base_url = "https://openrouter.ai/api/v1/chat/completions"
            # Use the free router – automatically picks the best available free model
            self.model = "openrouter/free"

    def paraphrase_article(self, title, content, category, min_words=500):
        """Paraphrase article using OpenRouter with consistent professional style."""
        if not self.api_key:
            return {'success': False, 'error': 'API key missing'}

        prompt = f"""You are a senior editor at a major Nigerian news publication. Your job is to rewrite news articles in a consistent, professional house style regardless of the original source or topic.
    
    HUMANIZATION RULES — CRITICAL:
    1. Write like a human journalist, not an AI. Vary sentence length — mix short punchy sentences with longer detailed ones.
    2. Use natural transitions between paragraphs — "Meanwhile", "However", "This comes as", "Speaking on the matter"
    3. Avoid repetitive sentence starters — never start three consecutive sentences with "The"
    4. Use contractions naturally where appropriate — "it's", "doesn't", "wasn't"
    5. Add journalistic colour — describe scenes, reactions, and atmosphere where the original allows
    6. Avoid AI giveaway phrases like "It is worth noting", "It is important to note", "In conclusion", "Furthermore", "Moreover", "In today's world"
    7. Never use the word "delve", "crucial", "pivotal", "game-changer", "landscape", "realm"
    8. Write the way a Nigerian journalist would — grounded, direct, with local context
    
    HOUSE STYLE RULES — ALWAYS FOLLOW:
    1. Tone: Authoritative, clear, and engaging. Never sensational or tabloid.
    2. Voice: Third person only. Never first person.
    3. Tense: Past tense for events that happened. Present tense for ongoing situations.
    4. Names: Use full name on first mention, surname only after.
    5. Numbers: Spell out one to nine. Use digits for 10 and above.
    6. Currency: Always specify currency — ₦ for naira, $ for dollars.
    7. Quotes: Use double quotation marks. Always attribute quotes clearly.
    8. Length: Minimum {min_words} words. No maximum.
    9. No sensational language — avoid words like "bombshell", "shocking", "explosive"
    10. No speculation — only report what is confirmed in the original article

    STRICT HTML FORMATTING — NO EXCEPTIONS:
    - Every paragraph MUST be wrapped in <p></p> tags
    - Use <h2> for main section headings — 2 to 3 per article
    - Use <h3> for sub-headings where needed
    - Use <strong> for key names, figures, and facts on first mention
    - Use <blockquote> for direct quotes longer than one sentence
    - NO bullet points, NO numbered lists, NO markdown, NO plain text outside tags

    REQUIRED ARTICLE STRUCTURE:
    <p>[Lead paragraph — answers who, what, when, where, why in 2-3 sentences. Most important fact first.]</p>

    <p>[Second paragraph — expands on the lead with key details and context.]</p>

    <h2>[Descriptive section heading]</h2>
    <p>[Body paragraph with supporting details.]</p>

    <p>[Body paragraph with background and context.]</p>

    <h2>[Another descriptive section heading]</h2>
    <p>[Further details, reactions, or implications.]</p>

    <p>[Closing paragraph — what happens next or broader significance.]</p>

    CATEGORY: {category}
    TITLE: {title}

    ORIGINAL CONTENT:
    {content[:8000]}

    REWRITE THE ARTICLE NOW IN PROPER HOUSE STYLE WITH HTML FORMATTING:"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://blogsphere.ng/",
            "X-Title": "BlogSphere News"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6,
            "max_tokens": 4096
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                text = data['choices'][0]['message']['content'].strip()

                # Strip any markdown code fences if model adds them
                text = re.sub(r'^```html\n?', '', text)
                text = re.sub(r'\n?```$', '', text)

                # Remove duplicate sentences
                sentences = re.split(r'(?<=[.!?])\s+', text)
                seen = set()
                unique = []
                for s in sentences:
                    norm = s.strip().lower()
                    if norm and norm not in seen:
                        seen.add(norm)
                        unique.append(s)
                text = ' '.join(unique)

                word_count = len(re.sub(r'<[^>]+>', '', text).split())
                summary = ' '.join(re.sub(r'<[^>]+>', '', text).split()[:200])

                return {
                    'success': True,
                    'content': text,
                    'summary': summary,
                    'word_count': word_count
                }
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate_response(self, prompt, temperature=0.7, max_tokens=4096):
        """Generic method for direct chat interactions (optional)."""
        if not self.api_key:
            return {'success': False, 'error': 'API key missing'}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://yourdomain.com",  # Change this!
            "X-Title": "BlogSphere News"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                text = data['choices'][0]['message']['content'].strip()
                word_count = len(text.split())
                return {
                    'success': True,
                    'content': text,
                    'word_count': word_count
                }
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class EnhancedNewsFetcher:
    """Enhanced news fetcher with robust scraping + OpenRouter AI."""

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
        },
        'thisday': {
            'base_url': 'https://www.thisdaylive.com',
            'category_urls': {
                'news': 'https://www.thisdaylive.com/index.php/feed/',
                'politics': 'https://www.thisdaylive.com/index.php/category/politics/feed/',
                'economy': 'https://www.thisdaylive.com/index.php/category/business/feed/',
                'technology': 'https://www.thisdaylive.com/index.php/category/technology/feed/',
                'entertainment': 'https://www.thisdaylive.com/index.php/category/entertainment/feed/',
            }
        },
        'premiumtimes': {
            'base_url': 'https://www.premiumtimesng.com',
            'category_urls': {
                'news': 'https://www.premiumtimesng.com/feed',
                'politics': 'https://www.premiumtimesng.com/category/news/politics-news/feed',
                'economy': 'https://www.premiumtimesng.com/category/business/feed',
                'technology': 'https://www.premiumtimesng.com/category/tech/feed',
                'entertainment': 'https://www.premiumtimesng.com/category/entertainment-news/feed',
                'sport': 'https://www.premiumtimesng.com/category/sports/feed',
            }
        },
        'pulse': {
            'base_url': 'https://www.pulse.ng',
            'category_urls': {
                'news': 'https://www.pulse.ng/rss',
                'entertainment': 'https://www.pulse.ng/entertainment/rss',
                'sport': 'https://www.pulse.ng/sports/rss',
                'politics': 'https://www.pulse.ng/politics/rss',
                'economy': 'https://www.pulse.ng/business/rss',
                'technology': 'https://www.pulse.ng/tech/rss',
            }
        },
    }

    # === SCRAPING & OPENROUTER PROCESSING ===

    @staticmethod
    def scrape_article_content(url):
        """Robust scraping with fallback to article description if available."""
        try:
            print(f"🔍 Scraping: {url[:70]}...")
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            ]
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.google.com/',
                'DNT': '1',
            }
            time.sleep(random.uniform(1, 3))

            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()

            consent_markers = ['Before you continue', 'Accept all', 'Reject all', 'cookies and data', 'privacy settings']
            if any(marker in response.text for marker in consent_markers):
                print("❌ Consent page detected – cannot scrape")
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
                '.post-content',
                '.entry-content',
                '.article-detail',
                '.article-text',
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
                print(f"⚠️  Scraped content too short ({len(full_text)} chars)")
                return None

            print(f"✅ Scraped {len(full_text)} characters")
            return full_text[:15000]

        except requests.exceptions.RequestException as e:
            print(f"❌ Scraping error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected scraping error: {e}")
            return None

    @staticmethod
    def rewrite_with_ai(title, content, source, category, min_words=500):
        """Use OpenRouter to paraphrase content – source parameter is ignored."""
        openrouter = OpenRouterService()
        if not openrouter.api_key:
            print("⚠️  OpenRouter not configured, cannot rewrite.")
            return None

        print(f"📝 Sending to OpenRouter for paraphrasing ({len(content)} chars)...")
        # We no longer pass the source to the paraphrasing method
        result = openrouter.paraphrase_article(title, content, category, min_words)

        if result['success']:
            print(f"✅ OpenRouter generated {result['word_count']} words")
            return {
                'content': result['content'],
                'summary': result['summary'],
                'word_count': result['word_count']
            }
        else:
            print(f"❌ OpenRouter error: {result.get('error')}")
            return None

    @staticmethod
    def process_article_with_ai(article_dict):
        """
        Process article: scrape content → OpenRouter rewrite.
        If scraping fails, fall back to the article's description.
        """
        try:
            url = article_dict.get('url', '')
            title = article_dict.get('title', '')

            print(f"\n{'=' * 60}")
            print(f"📰 Processing: {title[:50]}...")
            print(f"URL: {url[:60]}...")

            scraped_content = EnhancedNewsFetcher.scrape_article_content(url)

            if not scraped_content or len(scraped_content) < 200:
                print("⚠️  Scraping failed – falling back to RSS description")
                description = article_dict.get('description', '') or article_dict.get('title', '')
                if len(description) < 100:
                    description = title
                scraped_content = description
                print(f"📄 Using description ({len(scraped_content)} chars)")

            ai_result = EnhancedNewsFetcher.rewrite_with_ai(
                title=title,
                content=scraped_content,
                source=article_dict.get('source', 'Unknown'),  # still passed but ignored
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
                print("⚠️  OpenRouter failed – using fallback content")
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
            article_dict['content'] = article_dict.get('description', article_dict.get('title', 'No content'))
            article_dict['word_count'] = len(article_dict['content'].split())
            article_dict['ai_processed'] = False
            return article_dict

    # === NEWS FETCHING METHODS (with timeout fixes) ===

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
        """Fetch news from Google News using requests to avoid hanging."""
        try:
            source_key = 'google'
            category_url = EnhancedNewsFetcher.SOURCES[source_key]['category_urls'].get(
                category,
                EnhancedNewsFetcher.SOURCES[source_key]['base_url']
            )

            response = requests.get(category_url, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

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
        """Fetch from Nigerian RSS sources."""
        try:
            if source not in ['punch', 'vanguard', 'channels', 'thisday', 'premiumtimes', 'pulse']:
                return []

            feed_url = EnhancedNewsFetcher.SOURCES[source]['category_urls'].get(
                category,
                EnhancedNewsFetcher.SOURCES[source].get('base_url', '')
            )

            if not feed_url:
                return []

            response = requests.get(feed_url, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

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
        """Fetch from Reddit (already uses requests)."""
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
        """Fetch from BBC using requests with timeout."""
        try:
            feed_url = EnhancedNewsFetcher.SOURCES['bbc']['category_urls'].get(
                category, 'http://feeds.bbci.co.uk/news/rss.xml'
            )

            response = requests.get(feed_url, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

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
                elif source in ['punch', 'vanguard', 'channels', 'thisday', 'premiumtimes', 'pulse']:
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
                content=format_content(content),
                excerpt=article.get('description', '')[:200] or article.get('title', '')[:200],
                author=author,
                category=category_obj,
                published_date=timezone.now(),
            )

            post.tags.add('news')



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