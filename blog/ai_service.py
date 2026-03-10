# blog/ai_service.py - ENHANCED VERSION WITH AI CONTENT SUMMARIZATION
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
    """Enhanced news fetcher with multiple sources and AI content summarization"""

    # News source configurations
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

    @staticmethod
    def scrape_full_article_content(url):
        """Scrape the full article content from a URL"""
        try:
            print(f"🔍 Scraping content from: {url[:80]}...")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside',
                                 'iframe', 'noscript', 'form', 'button']):
                element.decompose()

            # Try to find main content area
            content_areas = []

            # Look for common article containers
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

            # If no specific content area found, use body
            if not content_areas:
                content_areas = [soup.body] if soup.body else [soup]

            # Extract text from content areas
            article_text = []
            for area in content_areas:
                # Get paragraphs
                paragraphs = area.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li'])
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 30:  # Only paragraphs with substantial content
                        article_text.append(text)

            # Join and clean the text
            full_text = '\n\n'.join(article_text)

            # Clean up whitespace
            full_text = re.sub(r'\n\s*\n+', '\n\n', full_text)
            full_text = re.sub(r' +', ' ', full_text)

            if len(full_text) < 100:
                print("⚠️  Article content too short, using fallback method")
                # Fallback: get all text
                full_text = soup.get_text(separator='\n', strip=True)
                full_text = re.sub(r'\n\s*\n+', '\n\n', full_text)

            print(f"✅ Scraped {len(full_text)} characters")
            return full_text[:10000]  # Limit to 10k characters

        except Exception as e:
            print(f"❌ Error scraping article: {e}")
            return None

    @staticmethod
    def summarize_and_rewrite_with_ai(article_title, article_content, source, category, min_words=500):
        """
        Use Google Gemini (FREE) to summarize and rewrite article content

        Args:
            article_title: The article title
            article_content: The scraped article content
            source: News source name
            category: Article category
            min_words: Minimum word count for output (default 500)

        Returns:
            dict with 'content', 'summary', and 'word_count'
        """
        try:
            # Get Gemini API key from environment or settings
            gemini_api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY', ''))

            if not gemini_api_key:
                print("⚠️  GEMINI_API_KEY not found. Set it in your environment variables.")
                print("   Get a free key at: https://makersuite.google.com/app/apikey")
                return {
                    'content': article_content[:2000] + "...",
                    'summary': article_content[:300],
                    'word_count': len(article_content.split())
                }

            print(f"🤖 Using AI to rewrite article (target: {min_words}+ words)...")

            # Prepare the prompt
            prompt = f"""You are a professional news writer. Rewrite the following news article in your own words.

REQUIREMENTS:
- Write at least {min_words} words
- Use original phrasing and sentence structure (DO NOT copy the original)
- Keep all important facts, quotes, and details
- Write in a clear, engaging journalistic style
- Maintain the news tone appropriate for the category: {category}
- Structure with introduction, main body, and conclusion
- Use proper paragraphs (separate with blank lines)

ORIGINAL ARTICLE:
Title: {article_title}
Source: {source}

Content:
{article_content[:5000]}

WRITE THE REWRITTEN ARTICLE NOW (minimum {min_words} words):"""

            # Call Gemini API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_api_key}"

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048,
                }
            }

            response = requests.post(url, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()

                # Extract the generated content
                if 'candidates' in data and len(data['candidates']) > 0:
                    generated_text = data['candidates'][0]['content']['parts'][0]['text']

                    # Clean up the text
                    generated_text = generated_text.strip()

                    # Calculate word count
                    word_count = len(generated_text.split())

                    # Create summary (first 200 words)
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

    # UPDATED: Fix for Google Cookie Consent Page Issue
    # Add this to the scrape_full_article_content method

    @staticmethod
    def scrape_full_article_content(url):
        """Scrape the full article content from a URL - FIXED for Google redirects"""
        try:
            print(f"🔍 Scraping content from: {url[:80]}...")

            # Check if it's a Google News redirect URL
            if 'news.google.com' in url:
                print("⚠️  Google News URL detected - attempting to extract real article URL...")
                try:
                    # Follow the redirect to get the real article URL
                    response = requests.get(url, allow_redirects=True, timeout=10)
                    real_url = response.url
                    print(f"✅ Redirected to: {real_url[:80]}...")
                    url = real_url
                except:
                    print("❌ Could not follow Google redirect")
                    return None

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()

            # Check if we got a cookie consent page
            if 'consent.google.com' in response.url or 'Before you continue' in response.text:
                print("❌ Hit Google consent page - cannot scrape")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside',
                                 'iframe', 'noscript', 'form', 'button']):
                element.decompose()

            # Try to find main content area
            content_areas = []

            # Look for common article containers
            article_selectors = [
                'article',
                '[class*="article-content"]',
                '[class*="post-content"]',
                '[class*="entry-content"]',
                '[class*="story-body"]',
                '[class*="article-body"]',
                '[class*="content-body"]',
                '[itemprop="articleBody"]',
                'main',
                '[role="main"]',
            ]

            for selector in article_selectors:
                elements = soup.select(selector)
                if elements:
                    content_areas.extend(elements)
                    break

            # If no specific content area found, use body
            if not content_areas:
                content_areas = [soup.body] if soup.body else [soup]

            # Extract text from content areas
            article_text = []
            for area in content_areas:
                # Get paragraphs
                paragraphs = area.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li'])
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 30:  # Only paragraphs with substantial content
                        article_text.append(text)

            # Join and clean the text
            full_text = '\n\n'.join(article_text)

            # Clean up whitespace
            full_text = re.sub(r'\n\s*\n+', '\n\n', full_text)
            full_text = re.sub(r' +', ' ', full_text)

            # Check if we actually got article content
            google_consent_indicators = [
                'Before you continue to Google',
                'Accept all',
                'Reject all',
                'Privacy settings',
                'cookies and data',
                'tailored ads'
            ]

            if any(indicator in full_text for indicator in google_consent_indicators):
                print("❌ Content appears to be consent page, rejecting")
                return None

            if len(full_text) < 200:
                print("⚠️  Article content too short, using fallback method")
                # Fallback: get all text
                full_text = soup.get_text(separator='\n', strip=True)
                full_text = re.sub(r'\n\s*\n+', '\n\n', full_text)

            print(f"✅ Scraped {len(full_text)} characters")
            return full_text[:10000]  # Limit to 10k characters

        except Exception as e:
            print(f"❌ Error scraping article: {e}")
            return None

    @staticmethod
    def process_article_with_ai(article_dict):
        """
        Process a single article: scrape content and rewrite with AI
        UPDATED: Better fallback handling
        """
        try:
            # Step 1: Try to scrape the full article content
            scraped_content = EnhancedNewsFetcher.scrape_full_article_content(article_dict['url'])

            # If scraping failed or content is the cookie consent page, use description
            if not scraped_content or len(scraped_content) < 200:
                print("⚠️  Could not scrape article, using RSS description + AI expansion")

                # Use the RSS description/summary as seed content
                seed_content = article_dict.get('description', '') or article_dict.get('content', '')

                if len(seed_content) < 50:
                    print("❌ Not enough content to work with")
                    article_dict[
                        'content'] = "Article content unavailable. Please visit the source link to read the full article."
                    article_dict['ai_processed'] = False
                    return article_dict

                # Ask AI to expand the description into a full article
                ai_result = EnhancedNewsFetcher.expand_description_with_ai(
                    article_title=article_dict['title'],
                    description=seed_content,
                    source=article_dict.get('source', 'Unknown'),
                    category=article_dict.get('category', 'NEWS'),
                    min_words=500
                )

                if ai_result:
                    article_dict['content'] = ai_result['content']
                    article_dict['description'] = ai_result['summary']
                    article_dict['word_count'] = ai_result['word_count']
                    article_dict['ai_processed'] = True
                    print(f"✅ Article expanded from description: {ai_result['word_count']} words")
                else:
                    article_dict['content'] = seed_content
                    article_dict['description'] = seed_content[:300]
                    article_dict['ai_processed'] = False

                return article_dict

            # Step 2: If we have good scraped content, rewrite with AI
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
                # Fallback to scraped content
                article_dict['content'] = scraped_content[:2000]
                article_dict['description'] = scraped_content[:300]
                article_dict['ai_processed'] = False
                print("⚠️  Using scraped content (AI failed)")

            return article_dict

        except Exception as e:
            print(f"❌ Error processing article: {e}")
            return article_dict

    @staticmethod
    def expand_description_with_ai(article_title, description, source, category, min_words=500):
        """
        NEW METHOD: Expand a short description into a full article using AI
        This is used when we can't scrape the full article content
        """
        try:
            gemini_api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY', ''))

            if not gemini_api_key:
                print("⚠️  GEMINI_API_KEY not found")
                return None

            print(f"🤖 Using AI to expand article from description (target: {min_words}+ words)...")

            # Prepare the prompt for expansion
            prompt = f"""You are a professional news writer. Based on the title and brief description below, write a comprehensive news article.

    REQUIREMENTS:
    - Write at least {min_words} words
    - Expand on the information provided in the description
    - Add context, background, and relevant details
    - Use professional journalistic style
    - Include what readers would want to know about this topic
    - Write in clear paragraphs (separate with blank lines)
    - Stay factual based on the description provided
    - Category: {category}

    ARTICLE INFORMATION:
    Title: {article_title}
    Source: {source}
    Brief Description: {description}

    Based on this information, write a comprehensive {min_words}+ word news article that expands on these details. Add context, explain the significance, and provide background information that would help readers understand the full story.

    WRITE THE FULL ARTICLE NOW:"""

            # Call Gemini API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_api_key}"

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.8,  # Slightly higher for creative expansion
                    "maxOutputTokens": 2048,
                }
            }

            response = requests.post(url, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()

                if 'candidates' in data and len(data['candidates']) > 0:
                    generated_text = data['candidates'][0]['content']['parts'][0]['text']
                    generated_text = generated_text.strip()
                    word_count = len(generated_text.split())
                    summary = ' '.join(generated_text.split()[:200])

                    print(f"✅ AI expanded to {word_count} words")

                    return {
                        'content': generated_text,
                        'summary': summary,
                        'word_count': word_count
                    }
                else:
                    print("❌ No content in AI response")
                    return None
            else:
                print(f"❌ Gemini API error: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error calling AI API: {e}")
            return None

    # === KEEP ALL YOUR EXISTING METHODS BELOW ===

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
    def fetch_google_news_by_category(category='news', limit=10, country=None):
        """Fetch news from Google News by specific category"""
        try:
            # Get the category URL or default to general news
            category_url = EnhancedNewsFetcher.SOURCES['google']['category_urls'].get(
                category,
                EnhancedNewsFetcher.SOURCES['google']['base_url']
            )

            feed = feedparser.parse(category_url)
            news_items = []

            for entry in feed.entries[:limit]:
                source_name = entry.get('source', {}).get('title', 'Google News')

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
            print(f"❌ Error fetching Google News ({category}): {e}")
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

            # Use AI-processed content if available
            content = article.get('content', '')

            # Create blog post
            post = Post.objects.create(
                title=article['title'][:200],
                slug=slug,
                content=content,
                excerpt=article.get('description', '')[:200] or article.get('title', '')[:200],
                author=author,
                category=category_obj,
                published_date=timezone.now(),
            )

            # Add tags
            post.tags.add('news', 'auto-generated', article.get('category', 'general').lower())

            if article.get('ai_processed'):
                post.tags.add('ai-rewritten')

            print(f"✅ Created blog post: {post.title}")
            return post

        except Exception as e:
            print(f"❌ Error generating blog post: {e}")
            return None

    @staticmethod
    def extract_content_from_url(url):
        """Extract main content from URL (legacy method, use scrape_full_article_content instead)"""
        return EnhancedNewsFetcher.scrape_full_article_content(url)


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