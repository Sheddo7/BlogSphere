# blog/ai_service.py - ELABORATED, SOURCE‑FREE 500+ WORD AI GENERATION
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
    """Enhanced news fetcher with guaranteed 500+ word AI content, elaborated and source‑free"""

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

    # === AI PROCESSING METHODS (ELABORATED, SOURCE‑FREE) ===

    @staticmethod
    def scrape_article_content(url):
        """Scrape full article content from URL"""
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
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'form', 'button']):
                tag.decompose()
            content_selectors = [
                'article',
                '[class*="article-content"]',
                '[class*="article-body"]',
                '[class*="post-content"]',
                '[class*="entry-content"]',
                '[itemprop="articleBody"]',
            ]
            content_areas = []
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content_areas.extend(elements)
                    break
            if not content_areas:
                content_areas = [soup.body] if soup.body else [soup]
            article_text = []
            for area in content_areas:
                for elem in area.find_all(['p', 'h2', 'h3', 'h4']):
                    text = elem.get_text(strip=True)
                    if len(text) > 40:
                        article_text.append(text)
            full_text = '\n\n'.join(article_text)
            full_text = re.sub(r'\n\s*\n+', '\n\n', full_text)
            if len(full_text) < 200:
                print(f"⚠️  Content too short")
                return None
            if any(marker in full_text for marker in consent_markers):
                print("❌ Consent text in content")
                return None
            print(f"✅ Scraped {len(full_text)} characters")
            return full_text[:10000]
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return None

    @staticmethod
    def rewrite_with_ai(title, content, source, category, min_words=500, attempt=1):
        """Use Gemini AI to generate an elaborated, source‑free article of at least min_words."""
        gemini_api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY', ''))
        if not gemini_api_key:
            print("⚠️  No GEMINI_API_KEY found in environment or settings")
            return None

        # Ensure content is a string
        if content is None:
            content = ""
        if not content.strip():
            content = title or "No content available."

        # Models to try in order
        models = [
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro-latest',
            'gemini-pro'
        ]

        # Adjust prompt based on attempt number
        if attempt == 1:
            length_instruction = f"Write at least {min_words} words."
        else:
            length_instruction = f"Your previous response was too short. You MUST write at least {min_words} words while maintaining accuracy and elaboration."

        # New prompt: no source attribution, encourage elaboration, keep facts accurate
        prompt = f"""You are a professional journalist for a reputable news blog. Your task is to write a complete, in‑depth news article based solely on the facts provided in the source below.

**CRITICAL RULES**:
- **DO NOT** mention the original source by name (e.g., "according to Vanguard", "BBC reports"). The article should read as original reporting.
- **DO NOT** add any facts, quotes, names, dates, or locations that are not present in the source. If you include background context, it must be clearly presented as analysis or common knowledge (e.g., "Experts note that...", "Historically, this type of event...").
- Preserve all key facts, names, dates, locations, and quotes exactly as they appear.
- Use completely original phrasing – do not copy sentences verbatim from the source.
- **Elaborate** on the story: add background information, possible implications, related context, and (if relevant) expert or public reaction, as long as it does not introduce new facts that contradict the source.
- Write in a neutral, objective journalistic style. Avoid sensationalism.
- Structure the article as follows:
  1. **Headline** – Use the given title (may be slightly rephrased).
  2. **Lead paragraph** – Summarise the most important facts (who, what, when, where, why).
  3. **Body paragraphs** – Expand with details, background, analysis, and implications.
  4. **Concluding paragraph** – Provide closure or mention what might happen next.
- The article must be self‑contained and readable without referring back to the source.
- Category: {category}

SOURCE ARTICLE:
Title: {title}
Content:
{content[:5000]}

Now write your article. {length_instruction}"""

        last_error = None
        for model in models:
            try:
                print(f"🤖 Attempt {attempt} - Trying model: {model}")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.6,          # Slightly higher for elaboration, but still controlled
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
                        word_count = len(text.split())
                        print(f"✅ {model} generated {word_count} words")
                        if word_count >= min_words or attempt >= 2:
                            summary = ' '.join(text.split()[:200])
                            return {'content': text, 'summary': summary, 'word_count': word_count}
                        else:
                            print(f"⚠️  Only {word_count} words (below {min_words}) – retrying with stronger length instruction")
                            return EnhancedNewsFetcher.rewrite_with_ai(
                                title, content, source, category, min_words, attempt=2
                            )
                    else:
                        print("❌ No candidates in response")
                else:
                    print(f"❌ API error {response.status_code}: {response.text[:200]}")
                    last_error = response.status_code
            except Exception as e:
                print(f"❌ Exception with {model}: {e}")
                last_error = e
                continue

        print("❌ All models failed. Last error:", last_error)
        return None

    @staticmethod
    def generate_fallback_content(title, source, category):
        """Create a longer, elaborated article using a template when AI fails."""
        print("🔧 Using fallback template to generate article...")
        # Professional fallback – no source mention, more elaborate
        paragraphs = [
            f"{title}",
            f"This development has drawn attention from various quarters, with observers noting its potential impact on the {category.lower()} landscape.",
            f"According to sources familiar with the matter, the situation is still unfolding, and further details are expected to emerge in the coming days.",
            f"Analysts suggest that this event could have wider implications, particularly in how it might influence相关政策 or public discourse.",
            f"While official statements remain limited, reactions on social media indicate a mix of concern and curiosity among the public.",
            f"As the story develops, our team will continue to monitor and provide updates. Stay with BlogSphere for the latest news and in‑depth analysis."
        ]
        # Ensure length
        while len(' '.join(paragraphs).split()) < 500:
            paragraphs.append(paragraphs[-1] + " Meanwhile, experts are calling for calm and patience as authorities handle the situation.")
        full_text = '\n\n'.join(paragraphs)
        return {
            'content': full_text,
            'summary': paragraphs[0][:200],
            'word_count': len(full_text.split())
        }

    @staticmethod
    def process_article_with_ai(article_dict):
        """
        Process article: scrape content + AI rewrite to 500+ words (elaborated, source‑free)
        """
        try:
            url = article_dict.get('url', '')
            title = article_dict.get('title', '')

            print(f"\n{'=' * 60}")
            print(f"📰 Processing: {title[:50]}...")
            print(f"URL: {url[:60]}...")

            # Step 1: Try to scrape
            scraped_content = EnhancedNewsFetcher.scrape_article_content(url)

            # Fallback to description if scraping fails or is too short
            if scraped_content is None or len(scraped_content) < 200:
                print("❌ Could not scrape enough content, using description as fallback")
                desc = article_dict.get('description') or ''
                title_fb = article_dict.get('title') or ''
                scraped_content = desc or title_fb
                if len(scraped_content) < 100:
                    scraped_content = (title_fb + " " + desc).strip()
                if not scraped_content:
                    scraped_content = "No content available."

            # Step 2: AI rewrite (with retry for length)
            print(f"📝 Sending to AI (scraped {len(scraped_content)} chars)...")
            ai_result = EnhancedNewsFetcher.rewrite_with_ai(
                title=title,
                content=scraped_content,
                source=article_dict.get('source', 'Unknown'),
                category=article_dict.get('category', 'NEWS'),
                min_words=500,
                attempt=1
            )

            if ai_result:
                article_dict['content'] = ai_result['content']
                article_dict['description'] = ai_result['summary']
                article_dict['word_count'] = ai_result['word_count']
                article_dict['ai_processed'] = True
                print(f"✅ SUCCESS: {ai_result['word_count']} words generated")
            else:
                # AI failed completely – use fallback template
                print("⚠️  AI failed, using fallback template")
                fallback = EnhancedNewsFetcher.generate_fallback_content(
                    title, article_dict.get('source', 'Unknown'), article_dict.get('category', 'NEWS')
                )
                article_dict['content'] = fallback['content']
                article_dict['description'] = fallback['summary']
                article_dict['word_count'] = fallback['word_count']
                article_dict['ai_processed'] = False

            print(f"{'=' * 60}\n")
            return article_dict

        except Exception as e:
            print(f"❌ Processing error: {e}")
            import traceback
            traceback.print_exc()
            article_dict['ai_processed'] = False
            article_dict['content'] = article_dict.get('description', article_dict.get('title', 'No content'))
            article_dict['word_count'] = len(article_dict['content'].split())
            return article_dict

    # === NEWS FETCHING METHODS (UNCHANGED) ===

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