# blog/ai_service.py - ENHANCED VERSION WITH GOOGLE GEMINI SUMMARISATION
import os
import requests
import json
from datetime import datetime
import feedparser
from django.conf import settings
from django.utils import timezone
from bs4 import BeautifulSoup
import time

# Google Gemini
try:
    import google.generativeai as genai
    GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY', ''))
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
        print("⚠️  Gemini API key not found. AI rewriting disabled.")
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google.generativeai not installed. Install with: pip install google-generativeai")


class EnhancedNewsFetcher:
    """Enhanced news fetcher with multiple sources and Gemini summarisation"""

    # News source configurations
    SOURCES = {
        'google': {
            'base_url': 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en',  # international
            'category_urls': {
                'news': 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en',
                'sport': 'https://news.google.com/rss/headlines/section/topic/SPORTS?hl=en-US&gl=US&ceid=US:en',
                'entertainment': 'https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-US&gl=US&ceid=US:en',
                'economy': 'https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en',
                'politics': 'https://news.google.com/rss/headlines/section/topic/POLITICS?hl=en-US&gl=US&ceid=US:en',
                'technology': 'https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en',
            }
        },
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

    # ===== FETCH METHODS (unchanged) =====
    @staticmethod
    def fetch_news_api(category='general', country='nigeria', limit=10):
        """Fetch news from NewsAPI"""
        api_key = getattr(settings, 'NEWS_API_KEY', os.environ.get('NEWS_API_KEY', ''))
        if not api_key:
            print("⚠️  NewsAPI key not found.")
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
                print(f"❌ NewsAPI error: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching NewsAPI: {e}")
            return []

    @staticmethod
    def fetch_google_news_by_category(category='news', limit=10, country=None):
        """Fetch news from Google News by specific category"""
        try:
            source_key = 'google_nigeria' if country == 'nigeria' else 'google'
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
        """Fetch news from multiple sources and categories"""
        if categories is None:
            categories = ['news', 'sport', 'entertainment', 'economy', 'politics', 'technology']
        if sources is None:
            sources = ['google', 'reddit', 'bbc']

        all_articles = []
        for source in sources:
            for category in categories:
                print(f"📡 Fetching {category} from {source}...")
                if source == 'google':
                    articles = EnhancedNewsFetcher.fetch_google_news_by_category(
                        category, limit=limit_per_source, country=None
                    )
                elif source == 'google_nigeria':
                    articles = EnhancedNewsFetcher.fetch_google_news_by_category(
                        category, limit=limit_per_source, country='nigeria'
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
                    all_articles.extend(articles)
                    print(f"✅ Found {len(articles)} articles from {source}/{category}")
                time.sleep(1)
        print(f"🎉 Total articles fetched: {len(all_articles)}")
        return all_articles

    # ===== GEMINI REWRITING =====
    @staticmethod
    def rewrite_with_gemini(text, target_words=500):
        """Use Google Gemini to rewrite an article in original words."""
        if not GEMINI_AVAILABLE:
            return text

        # Truncate input to avoid token limits (Gemini 1.5 Flash can handle ~1M tokens, but we keep it reasonable)
        text = text[:15000]  # roughly 3000–4000 words

        prompt = f"""
You are a professional journalist. Rewrite the following news article in your own words.
The new article should be original, well‑structured, and approximately {target_words} words long.
Do not copy sentences verbatim from the original. Include the key facts, but express them differently.

Original article:
{text}

Your rewritten article:
"""

        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            rewritten = response.text.strip()
            return rewritten
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            return text  # fallback to original

    # ===== MODIFIED: GENERATE BLOG POST WITH GEMINI =====
    @staticmethod
    def generate_blog_post_from_article(article, use_ai=True):
        """Generate a blog post from a news article, optionally using Gemini to rewrite."""
        from django.utils.text import slugify
        from django.contrib.auth.models import User
        from blog.models import Category, Post
        from django.utils import timezone

        try:
            category_name = article.get('category', 'NEWS')
            category_obj, _ = Category.objects.get_or_create(name=category_name)

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

            # --- Fetch full content if needed ---
            content_text = article.get('content', '')
            if len(content_text) < 500 and article.get('url'):
                print(f"📥 Fetching full content from {article['url']}")
                full_text = EnhancedNewsFetcher.extract_content_from_url(article['url'])
                if full_text and len(full_text) > len(content_text):
                    content_text = full_text

            # --- Apply Gemini rewriting if requested and possible ---
            if use_ai and content_text and len(content_text) > 200:
                gemini_rewrite = EnhancedNewsFetcher.rewrite_with_gemini(content_text)
                if gemini_rewrite and gemini_rewrite != content_text:
                    content_text = gemini_rewrite
                    print("✅ Used Gemini to rewrite content")

            # Truncate to a reasonable length
            MAX_CONTENT_CHARS = 15000  # increased for Gemini output
            if len(content_text) > MAX_CONTENT_CHARS:
                content_text = content_text[:MAX_CONTENT_CHARS] + "... [Content truncated]"

            # Build the post content with rich formatting
            enhanced_content = f"""
<h1>{article['title']}</h1>
<div class="alert alert-info">
    <strong>Source:</strong> {article.get('source', 'Unknown')}<br>
    <strong>Published:</strong> {article.get('published_at', 'N/A')}<br>
    <strong>Original URL:</strong> <a href="{article['url']}" target="_blank" rel="noopener">{article['url'][:100]}...</a>
</div>
<hr>
"""
            if article.get('description') and article['description'] not in content_text:
                enhanced_content += f"<h3>Summary</h3>\n<p>{article['description']}</p>\n<hr>\n"
            if content_text:
                enhanced_content += f"<h3>Article</h3>\n<div class='article-content'>{content_text}</div>\n<hr>\n"
            enhanced_content += f"""
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
                excerpt=article.get('description', '')[:300] or article.get('title', '')[:200],
                author=author,
                category=category_obj,
                published_date=timezone.now(),
            )
            post.tags.add('news', article.get('category', 'general').lower())
            print(f"✅ Created blog post: {post.title} ({len(content_text)} chars)")
            return post

        except Exception as e:
            print(f"❌ Error generating blog post: {e}")
            return None

    @staticmethod
    def extract_content_from_url(url):
        """Extract main content from URL (now up to 15k chars)."""
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
            return text[:15000]
        except Exception as e:
            print(f"❌ Error extracting content: {e}")
            return None

    # ===== COLLATION METHOD (optional) =====
    @staticmethod
    def collate_articles(articles, max_words=500):
        """
        Takes a list of article dicts, fetches full text for each,
        and asks Gemini to produce one coherent 500+ word article.
        Returns a single article dict ready for posting.
        """
        if not articles:
            return None

        full_texts = []
        sources = []
        for art in articles:
            print(f"📥 Fetching full text for: {art['title'][:50]}...")
            content = art.get('content', '')
            if len(content) < 500 and art.get('url'):
                content = EnhancedNewsFetcher.extract_content_from_url(art['url']) or ''
            if content:
                full_texts.append(f"--- Source: {art.get('source', 'Unknown')} ---\n{content}")
                sources.append(art.get('source', 'Unknown'))
            time.sleep(1)

        if not full_texts:
            return None

        combined = "\n\n".join(full_texts)
        summarizer = EnhancedNewsFetcher.get_summarizer()
        if summarizer:
            prompt = f"""
You are a journalist. Write a new, original news article of about {max_words} words based on the following information gathered from multiple sources.
Do not copy sentences verbatim. Synthesize the information into a coherent, engaging article with a headline.

Information:
{combined[:3000]}
"""
            try:
                generated = summarizer(
                    prompt,
                    max_length=max_words * 4,
                    min_length=max_words * 3,
                    do_sample=True,
                    temperature=0.7
                )[0]['summary_text']
                new_text = generated
            except Exception as e:
                print(f"❌ Generation failed: {e}")
                new_text = combined[:2000]
        else:
            new_text = combined[:2000]

        title = f"[Collated] {articles[0]['title'][:80]}"
        return {
            'title': title,
            'description': new_text[:300],
            'content': new_text,
            'url': ', '.join([a.get('url', '') for a in articles if a.get('url')]),
            'source': ' + '.join(set(sources)),
            'category': articles[0].get('category', 'NEWS'),
            'published_at': datetime.now().isoformat(),
            'image_url': articles[0].get('image_url', ''),
        }


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
        for cat, keywords in categories.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[cat] = score
        best = max(scores, key=scores.get)
        return best if scores[best] >= 2 else 'NEWS'
    @staticmethod
    def generate_summary(text, max_length=150):
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        sentences = text.split('. ')
        if len(sentences) <= 3:
            return text[:max_length] + '...'
        summary = sentences[0] + '. ' + sentences[-1]
        if len(summary) > max_length:
            summary = summary[:max_length] + '...'
        return summary
    @staticmethod
    def extract_content_from_url(url):
        return EnhancedNewsFetcher.extract_content_from_url(url)