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
        """Same as before – keep your existing method."""
        # ... (keep your existing implementation; not repeated for brevity)
        pass

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
        # ... (keep your existing method; unchanged)
        pass

    # ===== FETCH METHODS =====

    @staticmethod
    def fetch_news_api(category='general', country='ng', limit=10):
        """Same as before – with fallback."""
        # ... (keep your existing implementation)
        pass

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
        # ... unchanged
        pass

    @staticmethod
    def fetch_bbc_rss(category='news', limit=10):
        # ... unchanged
        pass

    @staticmethod
    def fetch_multiple_sources(categories=None, sources=None, limit_per_source=5):
        """Fetch with Nigerian sources first."""
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
                    print(f"✅ {len(arts)} articles from {source}/{cat}")
                else:
                    print(f"⚠️  No articles from {source}/{cat}")

                time.sleep(1)

        print(f"🎉 Total articles fetched: {len(all_articles)}")
        return all_articles

    @staticmethod
    def generate_blog_post_from_article(article):
        # ... unchanged
        pass


class SimpleNewsFetcher(EnhancedNewsFetcher):
    pass