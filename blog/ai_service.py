# blog/ai_service.py - SCRAPE + PARAPHRASE (LEGITIMATE NEWS, NO HALLUCINATIONS)
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


class EnhancedNewsFetcher:
    """News fetcher that scrapes original article and paraphrases it with AI (no fabrication)."""

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

    # === SCRAPING & PARAPHRASING ===

    @staticmethod
    def scrape_article_content(url):
        """Scrape full article content from URL – improved to get all paragraphs."""
        try:
            print(f"🔍 Scraping: {url[:70]}...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()
            consent_markers = ['Before you continue', 'Accept all', 'Reject all', 'cookies and data', 'privacy settings']
            if any(marker in response.text for marker in consent_markers):
                print("❌ Consent page detected")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'form', 'button']):
                tag.decompose()

            # Expanded list of selectors for article content
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
                    # Use the first matching element as the main content area
                    content_area = elements[0]
                    break

            if not content_area:
                # Fallback: use body
                content_area = soup.body

            if not content_area:
                return None

            # Extract all paragraphs from the content area
            paragraphs = content_area.find_all(['p', 'h2', 'h3', 'h4'])
            article_text = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 40:  # filter out very short lines
                    article_text.append(text)

            full_text = '\n\n'.join(article_text)
            full_text = re.sub(r'\n\s*\n+', '\n\n', full_text)

            if len(full_text) < 200:
                print(f"⚠️  Content too short ({len(full_text)} chars)")
                return None

            # Double-check for consent text
            if any(marker in full_text for marker in consent_markers):
                print("❌ Consent text in content")
                return None

            print(f"✅ Scraped {len(full_text)} characters")
            return full_text[:15000]  # increased limit

        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return None

    @staticmethod
    def paraphrase_with_ai(title, original_content, category, min_words=500):
        """
        Use Gemini AI to paraphrase the original article content.
        No new facts are added; the output is a unique rewrite preserving all details.
        """
        gemini_api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY', ''))
        if not gemini_api_key:
            print("⚠️  No GEMINI_API_KEY found")
            return None

        if not original_content or len(original_content) < 200:
            print("❌ Original content too short to paraphrase")
            return None

        # Models to try
        models = [
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro-latest',
            'gemini-pro'
        ]

        # Paraphrasing prompt – strict about not adding external info
        prompt = f"""You are a professional journalist. Your task is to **paraphrase** the following article content.

**RULES**:
- Do NOT add any new facts, quotes, names, dates, or locations that are not present in the original content.
- Do NOT change the meaning of any fact.
- Use completely original wording – rewrite every sentence in your own style.
- Preserve all key details, including names, numbers, quotes, and contextual information.
- If the original is short, you may elaborate by explaining terms or adding background that is **directly implied** by the text (e.g., defining an acronym, explaining a local reference), but do not invent.
- The output must be at least {min_words} words.
- Write in a neutral, professional journalistic tone.
- Category: {category}
- Do not mention the original source by name.

ORIGINAL ARTICLE TITLE: {title}
ORIGINAL ARTICLE CONTENT:
{original_content[:8000]}

Now write your paraphrased version:"""

        for model in models:
            try:
                print(f"🤖 Paraphrasing with {model}...")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.4,
                        "maxOutputTokens": 4096,
                        "topP": 0.95,
                        "topK": 40
                    }
                }
                response = requests.post(url, json=payload, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    if 'candidates' in data and len(data['candidates']) > 0:
                        text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                        # Basic cleanup of potential duplicates
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
                        print(f"✅ Generated {word_count} words")
                        summary = ' '.join(text.split()[:200])
                        return {'content': text, 'summary': summary, 'word_count': word_count}
                else:
                    print(f"❌ API error {response.status_code}")
            except Exception as e:
                print(f"❌ Exception with {model}: {e}")
                continue

        print("❌ All paraphrasing attempts failed")
        return None

    @staticmethod
    def process_article_with_ai(article_dict):
        """
        Process article: scrape original content -> paraphrase with AI.
        Returns None if scraping fails or content is insufficient.
        """
        try:
            url = article_dict.get('url', '')
            title = article_dict.get('title', '')

            print(f"\n{'=' * 60}")
            print(f"📰 Processing: {title[:50]}...")
            print(f"URL: {url[:60]}...")

            # Step 1: Scrape the original article
            scraped_content = EnhancedNewsFetcher.scrape_article_content(url)

            if not scraped_content or len(scraped_content) < 300:
                print("❌ Failed to scrape enough original content. Aborting.")
                return None

            # Step 2: Paraphrase with AI
            print(f"📝 Sending to AI for paraphrasing ({len(scraped_content)} chars)...")
            ai_result = EnhancedNewsFetcher.paraphrase_with_ai(
                title=title,
                original_content=scraped_content,
                category=article_dict.get('category', 'NEWS'),
                min_words=500
            )

            if ai_result:
                article_dict['content'] = ai_result['content']
                article_dict['description'] = ai_result['summary']
                article_dict['word_count'] = ai_result['word_count']
                article_dict['ai_processed'] = True
                print(f"✅ SUCCESS: {ai_result['word_count']} words paraphrased")
            else:
                # If paraphrasing fails, fall back to scraped content (truncated)
                print("⚠️  Paraphrasing failed, using scraped content as fallback")
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

    # === NEWS FETCHING METHODS (unchanged, keep your existing implementations) ===
    @staticmethod
    def fetch_news_api(category='general', country='nigeria', limit=10):
        # ... (your existing code) ...
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
        # ... (your existing code) ...
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
        # ... (your existing code) ...
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
        # ... (your existing code) ...
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
        # ... (your existing code) ...
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
        # ... (your existing code) ...
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
        """Generate blog post from article (used by other endpoints)"""
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
        # ... unchanged ...
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