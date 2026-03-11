# blog/ai_service.py - PROFESSIONAL VERSION WITH NIGERIAN RSS DEBUGGING
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
    """News fetcher with Nigerian priority and professional AI rewriting (500+ words)."""

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
            },
            'main_feed': 'https://punchng.com/feed/'
        },
        'vanguard': {
            'base_url': 'https://www.vanguardngr.com',
            'category_urls': {
                'news': 'https://www.vanguardngr.com/feed/',
                'sport': 'https://www.vanguardngr.com/category/sports/feed/',
                'entertainment': 'https://www.vanguardngr.com/category/entertainment/feed/',
                'economy': 'https://www.vanguardngr.com/category/business/feed/',
                'politics': 'https://www.vanguardngr.com/category/politics/feed/',
            },
            'main_feed': 'https://www.vanguardngr.com/feed/'
        },
        'channels': {
            'base_url': 'https://www.channelstv.com',
            'category_urls': {
                'news': 'https://www.channelstv.com/feed/',
                'sport': 'https://www.channelstv.com/category/sports/feed/',
                'entertainment': 'https://www.channelstv.com/category/entertainment/feed/',
                'politics': 'https://www.channelstv.com/category/politics/feed/',
            },
            'main_feed': 'https://www.channelstv.com/feed/'
        }
    }

    CONSENT_MARKERS = [
        'before you continue', 'accept all', 'reject all', 'consent.google.com',
        'cookies and data', 'privacy settings', 'deliver and maintain google services',
        'track outages', 'measure audience engagement', 'personalized content',
        'personalized ads', 'g.co/privacytools'
    ]

    @staticmethod
    def scrape_full_article_content(url):
        """Scrape full article content – returns None if fails or consent page."""
        try:
            print(f"🔍 Scraping content from: {url[:80]}...")

            if 'news.google.com' in url:
                print("⛔ Skipping Google News URL")
                return None

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            text_lower = response.text.lower()
            for marker in EnhancedNewsFetcher.CONSENT_MARKERS:
                if marker in text_lower:
                    print(f"❌ Consent page detected")
                    return None

            soup = BeautifulSoup(response.content, 'html.parser')
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside',
                                 'iframe', 'noscript', 'form', 'button', 'advertisement']):
                element.decompose()

            selectors = [
                'article', '[class*="article-content"]', '[class*="post-content"]',
                '[class*="entry-content"]', '[class*="story-body"]', '[class*="article-body"]',
                'main', '[role="main"]'
            ]
            content_area = None
            for sel in selectors:
                elems = soup.select(sel)
                if elems:
                    content_area = elems[0]
                    break
            if not content_area:
                content_area = soup.body or soup

            paragraphs = content_area.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li'])
            text_parts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40]
            full_text = '\n\n'.join(text_parts)

            if len(full_text) < 300:
                # fallback to all text
                full_text = soup.get_text(separator='\n', strip=True)
                full_text = re.sub(r'\n\s*\n+', '\n\n', full_text)

            for marker in EnhancedNewsFetcher.CONSENT_MARKERS:
                if marker in full_text.lower():
                    print("❌ Content contains consent text")
                    return None

            print(f"✅ Scraped {len(full_text)} chars")
            return full_text[:12000]  # limit

        except Exception as e:
            print(f"❌ Scrape error: {e}")
            return None

    @staticmethod
    def summarize_and_rewrite_with_ai(article_title, article_content, source, category, min_words=500):
        """Force AI to write at least min_words words of professional journalism."""
        try:
            gemini_api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY', ''))
            if not gemini_api_key:
                print("⚠️  No GEMINI_API_KEY, using original.")
                return {
                    'content': article_content[:2000] + "...",
                    'summary': article_content[:300],
                    'word_count': len(article_content.split())
                }

            print(f"🤖 AI rewriting (target: {min_words}+ words) – professional style...")

            prompt = f"""You are an award-winning journalist writing for a major news publication. Rewrite the following news article from scratch, following strict professional guidelines.

**ABSOLUTE REQUIREMENTS:**
- Write at least {min_words} words. Count your words to ensure this minimum is met.
- Use flawless, formal, journalistic English – no slang, no markdown, no bullet points.
- Do NOT copy any sentence from the original – paraphrase everything completely.
- Structure the article: start with a compelling lead (who, what, when, where, why), then develop with background, quotes (if any), and end with context or future implications.
- Maintain a neutral, factual tone suitable for the category: {category}.
- Correct any spelling, grammar, or punctuation errors you notice.
- Separate paragraphs with blank lines for readability.

**ORIGINAL ARTICLE:**
Title: {article_title}
Source: {source}

Content:
{article_content[:5000]}

**YOUR PROFESSIONAL REWRITE (minimum {min_words} words):**"""

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_api_key}"
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048,
                }
            }
            response = requests.post(url, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                    # Post‑process
                    text = re.sub(r'\*\*|__', '', text)                     # remove bold
                    text = re.sub(r'^\s*[-•*]\s*', '', text, flags=re.MULTILINE)  # remove bullets
                    text = re.sub(r'\n{3,}', '\n\n', text)                 # max two newlines
                    text = re.sub(r'[ \t]+', ' ', text)                    # collapse spaces
                    word_count = len(text.split())

                    # If still below min_words, we could append original, but better to trust AI
                    if word_count < min_words:
                        print(f"⚠️  AI only gave {word_count} words – extending with original summary")
                        # Append some original content to reach minimum
                        needed = min_words - word_count
                        extra = ' '.join(article_content.split()[:needed*10])  # rough
                        text += "\n\n" + extra
                        word_count = len(text.split())

                    summary = ' '.join(text.split()[:200])
                    print(f"✅ AI generated {word_count} words")
                    return {
                        'content': text,
                        'summary': summary,
                        'word_count': word_count
                    }
                else:
                    print("❌ No AI response content")
                    return None
            else:
                print(f"❌ Gemini error {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ AI exception: {e}")
            return None

    @staticmethod
    def process_article_with_ai(article_dict):
        """Scrape and rewrite, ensure 500+ words."""
        try:
            if 'news.google.com' in article_dict.get('url', ''):
                print("⛔ Skipping Google News")
                article_dict['content'] = f"<p><a href='{article_dict['url']}'>Read at source</a></p>"
                article_dict['ai_processed'] = False
                return article_dict

            scraped = EnhancedNewsFetcher.scrape_full_article_content(article_dict['url'])
            if not scraped or len(scraped) < 200:
                print("⚠️  Using description as fallback")
                article_dict['content'] = article_dict.get('description', '')
                return article_dict

            ai = EnhancedNewsFetcher.summarize_and_rewrite_with_ai(
                article_title=article_dict['title'],
                article_content=scraped,
                source=article_dict.get('source', 'Unknown'),
                category=article_dict.get('category', 'NEWS'),
                min_words=500
            )

            if ai:
                article_dict['content'] = ai['content']
                article_dict['description'] = ai['summary']
                article_dict['word_count'] = ai['word_count']
                article_dict['ai_processed'] = True
            else:
                article_dict['content'] = scraped[:3000]
                article_dict['description'] = scraped[:300]
                article_dict['ai_processed'] = False

            return article_dict

        except Exception as e:
            print(f"❌ process_article error: {e}")
            return article_dict

    # ===== FETCH METHODS =====

    @staticmethod
    def fetch_news_api(category='general', country='ng', limit=10):
        """NewsAPI with fallback."""
        api_key = getattr(settings, 'NEWS_API_KEY', os.environ.get('NEWS_API_KEY', ''))
        if not api_key:
            print("❌ NEWS_API_KEY missing")
            return []

        print(f"📡 NewsAPI {category}/{country}...")
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            'apiKey': api_key,
            'category': category,
            'country': country,
            'pageSize': limit,
            'language': 'en'
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') != 'ok':
                    print(f"   API error: {data.get('message')}")
                    return []
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
                if not articles and country == 'ng':
                    print("⚠️  No NG articles, falling back to US")
                    return EnhancedNewsFetcher.fetch_news_api(category, 'us', limit)
                return articles
            else:
                print(f"❌ HTTP {resp.status_code}")
                return []
        except Exception as e:
            print(f"❌ NewsAPI error: {e}")
            return []

    @staticmethod
    def fetch_nigerian_rss(source, category='news', limit=10):
        """Robust RSS fetching with detailed logging and fallback to main feed."""
        if source not in ['punch', 'vanguard', 'channels']:
            return []

        # Determine feed URL
        feed_url = EnhancedNewsFetcher.SOURCES[source]['category_urls'].get(category)
        if not feed_url:
            feed_url = EnhancedNewsFetcher.SOURCES[source].get('main_feed')

        print(f"📡 {source}/{category} RSS: {feed_url}")

        # Step 1: Fetch with requests to check accessibility
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        try:
            resp = requests.get(feed_url, headers=headers, timeout=10)
            print(f"   HTTP status: {resp.status_code}, content length: {len(resp.text)}")
            if resp.status_code != 200:
                print(f"   ⚠️  Non-200 status, trying main feed...")
                main_feed = EnhancedNewsFetcher.SOURCES[source].get('main_feed')
                if main_feed and main_feed != feed_url:
                    resp = requests.get(main_feed, headers=headers, timeout=10)
                    feed_url = main_feed
                    print(f"   Main feed status: {resp.status_code}, length: {len(resp.text)}")
                else:
                    return []
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            return []

        # Step 2: Parse with feedparser
        feed = feedparser.parse(feed_url)
        print(f"   feedparser entries count: {len(feed.entries)}")

        # If no entries, try main feed again as last resort
        if not feed.entries:
            main_feed = EnhancedNewsFetcher.SOURCES[source].get('main_feed')
            if main_feed and main_feed != feed_url:
                print(f"   ⚠️  No entries, falling back to main feed: {main_feed}")
                feed = feedparser.parse(main_feed)
                print(f"   Main feed entries: {len(feed.entries)}")

        items = []
        for idx, entry in enumerate(feed.entries[:limit]):
            if not entry.get('title') or not entry.get('link'):
                print(f"   Skipping entry {idx}: missing title or link")
                continue
            items.append({
                'title': entry.title,
                'description': entry.get('summary', ''),
                'content': entry.get('summary', ''),
                'url': entry.link,
                'published_at': entry.get('published', ''),
                'source': source.capitalize(),
                'category': category.upper(),
            })
        print(f"   Returning {len(items)} articles")
        return items

    @staticmethod
    def fetch_reddit_by_category(category='news', limit=10):
        subreddit = EnhancedNewsFetcher.SOURCES['reddit']['subreddits'].get(category, 'news')
        url = f'https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}'
        headers = {'User-agent': 'newsbot/1.0'}
        try:
            print(f"📡 Reddit r/{subreddit}...")
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = []
                for p in data['data']['children']:
                    post = p['data']
                    items.append({
                        'title': post['title'],
                        'description': post.get('selftext', '')[:200],
                        'content': post.get('selftext', ''),
                        'url': f"https://reddit.com{post['permalink']}",
                        'published_at': datetime.fromtimestamp(post['created_utc']).isoformat(),
                        'source': f"Reddit r/{subreddit}",
                        'category': category.upper(),
                    })
                return items
            else:
                print(f"❌ Reddit error {resp.status_code}")
                return []
        except Exception as e:
            print(f"❌ Reddit exception: {e}")
            return []

    @staticmethod
    def fetch_bbc_rss(category='news', limit=10):
        feed_url = EnhancedNewsFetcher.SOURCES['bbc']['category_urls'].get(category, 'http://feeds.bbci.co.uk/news/rss.xml')
        print(f"📡 BBC/{category} RSS")
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
        """Fetch news, Nigerian sources first."""
        if categories is None:
            categories = ['news', 'sport', 'entertainment', 'economy', 'politics', 'technology']
        if sources is None:
            sources = ['punch', 'vanguard', 'channels', 'newsapi', 'bbc', 'reddit']

        all_articles = []
        for source in sources:
            for cat in categories:
                print(f"📡 Fetching {source}/{cat}...")
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
                else:
                    print(f"⚠️  No articles")
                time.sleep(1)

        print(f"🎉 Total fetched: {len(all_articles)}")
        return all_articles

    @staticmethod
    def generate_blog_post_from_article(article):
        from django.utils.text import slugify
        from django.contrib.auth.models import User
        from blog.models import Category, Post
        from django.utils import timezone

        try:
            cat_name = article.get('category', 'NEWS')
            category_obj, _ = Category.objects.get_or_create(name=cat_name)

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
            print(f"✅ Post created: {post.title}")
            return post
        except Exception as e:
            print(f"❌ Post creation error: {e}")
            return None


class SimpleNewsFetcher(EnhancedNewsFetcher):
    pass