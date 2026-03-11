# blog/ai_service.py - PROFESSIONAL VERSION WITH NIGERIAN RSS FALLBACK
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
    """News fetcher with Nigerian priority and professional AI rewriting."""

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
        """Scrape the full article content from a URL – returns None if consent page."""
        try:
            print(f"🔍 Scraping content from: {url[:80]}...")

            # Skip Google News URLs entirely (should not happen, but safety)
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

            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside',
                                 'iframe', 'noscript', 'form', 'button', 'advertisement']):
                element.decompose()

            # Try to find main content area
            content_areas = []
            article_selectors = [
                'article',
                '[class*="article-content"]',
                '[class*="post-content"]',
                '[class*="entry-content"]',
                '[class*="story-body"]',
                '[class*="article-body"]',
                'main',
                '[role="main"]',
            ]
            for selector in article_selectors:
                elements = soup.select(selector)
                if elements:
                    content_areas.extend(elements)
                    break

            if not content_areas:
                content_areas = [soup.body] if soup.body else [soup]

            # Extract text from content areas
            article_text = []
            for area in content_areas:
                paragraphs = area.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li'])
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 40:
                        article_text.append(text)

            full_text = '\n\n'.join(article_text)

            # Clean up whitespace
            full_text = re.sub(r'\n\s*\n+', '\n\n', full_text)
            full_text = re.sub(r' +', ' ', full_text)

            if len(full_text) < 300:
                print(f"⚠️  Article content too short ({len(full_text)} chars)")
                # Fallback: get all text
                full_text = soup.get_text(separator='\n', strip=True)
                full_text = re.sub(r'\n\s*\n+', '\n\n', full_text)

            # Final consent check on extracted text
            for marker in EnhancedNewsFetcher.CONSENT_MARKERS:
                if marker in full_text.lower():
                    print(f"❌ Content contains consent marker: {marker}")
                    return None

            print(f"✅ Scraped {len(full_text)} characters")
            return full_text[:12000]  # Limit to 12k characters

        except Exception as e:
            print(f"❌ Error scraping article: {e}")
            return None

    @staticmethod
    def summarize_and_rewrite_with_ai(article_title, article_content, source, category, min_words=500):
        """Enhanced professional AI rewriting with strict journalistic style."""
        try:
            gemini_api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY', ''))
            if not gemini_api_key:
                print("⚠️  GEMINI_API_KEY not found, using original content.")
                return {
                    'content': article_content[:2000] + "...",
                    'summary': article_content[:300],
                    'word_count': len(article_content.split())
                }

            print(f"🤖 Using AI to rewrite article professionally (target: {min_words}+ words)...")
            prompt = f"""You are an experienced journalist for a reputable news outlet. Rewrite the following news article in your own words.

**IMPORTANT REQUIREMENTS:**
- Write at least {min_words} words.
- Use **professional, fluent, and grammatically correct** journalistic English.
- Do NOT copy sentences from the original – rephrase everything.
- Maintain a neutral, factual tone appropriate for the category: {category}.
- Structure the article with an engaging headline-style lead, body paragraphs, and a concluding sentence.
- Use proper paragraphs separated by blank lines.
- Avoid markdown, bullet points, or any formatting symbols – just plain text.
- Correct any spelling or punctuation errors you find in the original.

**ORIGINAL ARTICLE:**
Title: {article_title}
Source: {source}

Content:
{article_content[:5000]}

**WRITE THE REWRITTEN ARTICLE NOW (minimum {min_words} words):**"""

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
                    generated_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                    # Post-process: remove any leftover markdown like ** or bullet points
                    generated_text = re.sub(r'\*\*|__', '', generated_text)  # remove bold markers
                    generated_text = re.sub(r'^\s*[-•*]\s*', '', generated_text, flags=re.MULTILINE)  # remove list markers
                    generated_text = re.sub(r'\n{3,}', '\n\n', generated_text)  # max two newlines
                    word_count = len(generated_text.split())
                    summary = ' '.join(generated_text.split()[:200])
                    print(f"✅ AI generated {word_count} words")
                    return {
                        'content': generated_text,
                        'summary': summary,
                        'word_count': word_count
                    }
                else:
                    print("❌ No content in AI response")
                    return None
            else:
                print(f"❌ Gemini API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error calling AI API: {e}")
            return None

    @staticmethod
    def process_article_with_ai(article_dict):
        """Process a single article: scrape content and rewrite with AI."""
        try:
            # Skip if URL is Google News (though they shouldn't be here)
            if 'news.google.com' in article_dict.get('url', ''):
                print("⛔ Skipping Google News article")
                article_dict['content'] = f"<p>This article is from Google News. <a href='{article_dict['url']}' target='_blank'>Read original</a></p>"
                article_dict['ai_processed'] = False
                return article_dict

            # Step 1: Scrape the full article content
            scraped_content = EnhancedNewsFetcher.scrape_full_article_content(article_dict['url'])

            if not scraped_content or len(scraped_content) < 100:
                print("⚠️  Could not scrape enough content, using description")
                article_dict['content'] = article_dict.get('description', '')
                return article_dict

            # Step 2: Rewrite with AI
            ai_result = EnhancedNewsFetcher.summarize_and_rewrite_with_ai(
                article_title=article_dict['title'],
                article_content=scraped_content,
                source=article_dict.get('source', 'Unknown'),
                category=article_dict.get('category', 'NEWS'),
                min_words=500
            )

            if ai_result:
                article_dict['content'] = ai_result['content']
                article_dict['description'] = ai_result['summary']
                article_dict['word_count'] = ai_result['word_count']
                article_dict['ai_processed'] = True
                print(f"✅ Article processed: {ai_result['word_count']} words")
            else:
                article_dict['content'] = scraped_content[:2000]
                article_dict['description'] = scraped_content[:300]
                article_dict['ai_processed'] = False
                print("⚠️  Using scraped content (AI failed)")

            return article_dict

        except Exception as e:
            print(f"❌ Error processing article: {e}")
            return article_dict

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
        """Fetch from Nigerian RSS with fallback to main feed if category feed empty."""
        if source not in ['punch', 'vanguard', 'channels']:
            return []

        # Try category-specific feed first
        feed_url = EnhancedNewsFetcher.SOURCES[source]['category_urls'].get(category)
        if not feed_url:
            feed_url = EnhancedNewsFetcher.SOURCES[source].get('main_feed')

        print(f"📡 {source}/{category} RSS: {feed_url}")
        feed = feedparser.parse(feed_url)

        # Check if feed has entries
        if not feed.entries:
            print(f"⚠️  No entries in {source}/{category} feed, trying main feed...")
            main_feed = EnhancedNewsFetcher.SOURCES[source].get('main_feed')
            if main_feed and main_feed != feed_url:
                feed = feedparser.parse(main_feed)
                print(f"   Main feed entries: {len(feed.entries)}")

        items = []
        for entry in feed.entries[:limit]:
            # Skip if title or link missing
            if not entry.get('title') or not entry.get('link'):
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
        print(f"   Found {len(items)} articles from {source}/{category}")
        return items

    @staticmethod
    def fetch_reddit_by_category(category='news', limit=10):
        """Fetch from Reddit."""
        subreddit = EnhancedNewsFetcher.SOURCES['reddit']['subreddits'].get(category, 'news')
        url = f'https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}'
        headers = {'User-agent': 'newsbot/1.0'}
        try:
            print(f"📡 Reddit r/{subreddit}...")
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
                print(f"❌ Reddit error: {resp.status_code}")
                return []
        except Exception as e:
            print(f"❌ Reddit exception: {e}")
            return []

    @staticmethod
    def fetch_bbc_rss(category='news', limit=10):
        """Fetch from BBC RSS."""
        feed_url = EnhancedNewsFetcher.SOURCES['bbc']['category_urls'].get(category, 'http://feeds.bbci.co.uk/news/rss.xml')
        print(f"📡 BBC/{category} RSS: {feed_url}")
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
        """Fetch from multiple sources. Nigerian sources are prioritized by default."""
        if categories is None:
            categories = ['news', 'sport', 'entertainment', 'economy', 'politics', 'technology']
        if sources is None:
            # Nigerian sources first, then NewsAPI, then international
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
                    print(f"✅ Found {len(arts)} articles from {source}/{cat}")
                else:
                    print(f"⚠️  No articles from {source}/{cat}")

                # Avoid rate limiting
                time.sleep(1)

        print(f"🎉 Total articles fetched: {len(all_articles)}")
        return all_articles

    @staticmethod
    def generate_blog_post_from_article(article):
        """Generate a blog post from a news article."""
        from django.utils.text import slugify
        from django.contrib.auth.models import User
        from blog.models import Category, Post
        from django.utils import timezone

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
            print(f"❌ Error generating blog post: {e}")
            return None


# Keep SimpleNewsFetcher for backward compatibility (now just inherits)
class SimpleNewsFetcher(EnhancedNewsFetcher):
    pass