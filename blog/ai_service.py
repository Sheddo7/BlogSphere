# blog/ai_service.py
import os
import requests
import feedparser
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from bs4 import BeautifulSoup
import time


# ── Google News RSS URLs ──────────────────────────────────────────────────────
# These use geo-targeting so results are actually latest Nigerian news
GOOGLE_NEWS_NIGERIA = {
    'news':          'https://news.google.com/rss/search?q=Nigeria&hl=en-NG&gl=NG&ceid=NG:en',
    'sport':         'https://news.google.com/rss/search?q=Nigeria+football+sport+Super+Eagles&hl=en-NG&gl=NG&ceid=NG:en',
    'entertainment': 'https://news.google.com/rss/search?q=Nigeria+Nollywood+entertainment+music+Afrobeats&hl=en-NG&gl=NG&ceid=NG:en',
    'economy':       'https://news.google.com/rss/search?q=Nigeria+economy+naira+CBN+dollar+inflation&hl=en-NG&gl=NG&ceid=NG:en',
    'politics':      'https://news.google.com/rss/search?q=Nigeria+politics+Tinubu+government+NASS&hl=en-NG&gl=NG&ceid=NG:en',
    'technology':    'https://news.google.com/rss/search?q=Nigeria+technology+fintech+startup+tech&hl=en-NG&gl=NG&ceid=NG:en',
}

# Google News general topic feeds
GOOGLE_NEWS_GLOBAL = {
    'news':          'https://news.google.com/rss?hl=en-NG&gl=NG&ceid=NG:en',
    'sport':         'https://news.google.com/rss/headlines/section/topic/SPORTS?hl=en-NG&gl=NG&ceid=NG:en',
    'entertainment': 'https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-NG&gl=NG&ceid=NG:en',
    'economy':       'https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-NG&gl=NG&ceid=NG:en',
    'politics':      'https://news.google.com/rss/headlines/section/topic/POLITICS?hl=en-NG&gl=NG&ceid=NG:en',
    'technology':    'https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-NG&gl=NG&ceid=NG:en',
}

# Nigerian RSS outlets
NIGERIAN_RSS = {
    'punch': {
        'news':          'https://punchng.com/feed/',
        'sport':         'https://punchng.com/category/sports/feed/',
        'entertainment': 'https://punchng.com/category/entertainment/feed/',
        'economy':       'https://punchng.com/category/business/feed/',
        'politics':      'https://punchng.com/category/politics/feed/',
    },
    'vanguard': {
        'news':          'https://www.vanguardngr.com/feed/',
        'sport':         'https://www.vanguardngr.com/category/sports/feed/',
        'entertainment': 'https://www.vanguardngr.com/category/entertainment/feed/',
        'economy':       'https://www.vanguardngr.com/category/business/feed/',
        'politics':      'https://www.vanguardngr.com/category/politics/feed/',
    },
    'channels': {
        'news':          'https://www.channelstv.com/feed/',
        'politics':      'https://www.channelstv.com/category/politics/feed/',
        'economy':       'https://www.channelstv.com/category/business/feed/',
        'entertainment': 'https://www.channelstv.com/category/entertainment/feed/',
        'sport':         'https://www.channelstv.com/category/sports/feed/',
    },
    'thisday': {
        'news':          'https://www.thisdaylive.com/feed/',
        'economy':       'https://www.thisdaylive.com/category/business/feed/',
        'politics':      'https://www.thisdaylive.com/category/politics/feed/',
        'sport':         'https://www.thisdaylive.com/category/sports/feed/',
    },
    'guardian_ng': {
        'news':          'https://guardian.ng/feed/',
        'sport':         'https://guardian.ng/sport/feed/',
        'entertainment': 'https://guardian.ng/entertainment/feed/',
        'economy':       'https://guardian.ng/business-services/feed/',
        'politics':      'https://guardian.ng/politics/feed/',
    },
    'thecable': {
        'news':          'https://www.thecable.ng/feed',
        'politics':      'https://www.thecable.ng/category/politics/feed',
        'economy':       'https://www.thecable.ng/category/business/feed',
    },
    'premiumtimes': {
        'news':          'https://www.premiumtimesng.com/feed',
        'politics':      'https://www.premiumtimesng.com/news/top-news/feed',
        'sport':         'https://www.premiumtimesng.com/sports/feed',
    },
}

BBC_RSS = {
    'news':          'http://feeds.bbci.co.uk/news/rss.xml',
    'sport':         'http://feeds.bbci.co.uk/sport/rss.xml',
    'entertainment': 'http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml',
    'economy':       'http://feeds.bbci.co.uk/news/business/rss.xml',
    'technology':    'http://feeds.bbci.co.uk/news/technology/rss.xml',
    'politics':      'http://feeds.bbci.co.uk/news/politics/rss.xml',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
}


class EnhancedNewsFetcher:

    SOURCES = {
        'google': {'category_urls': GOOGLE_NEWS_GLOBAL},
        'google_nigeria': {'category_urls': GOOGLE_NEWS_NIGERIA},
        'nigerian_sources': NIGERIAN_RSS,
        'bbc': {'category_urls': BBC_RSS},
    }

    @staticmethod
    def _parse_image(entry):
        """Extract image URL from RSS entry."""
        if hasattr(entry, 'media_content') and entry.media_content:
            return entry.media_content[0].get('url', '')
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            return entry.media_thumbnail[0].get('url', '')
        if hasattr(entry, 'enclosures') and entry.enclosures:
            enc = entry.enclosures[0]
            if 'image' in enc.get('type', ''):
                return enc.get('href', '')
        # Try to pull image from summary HTML
        summary = entry.get('summary', '')
        if '<img' in summary:
            try:
                soup = BeautifulSoup(summary, 'html.parser')
                img = soup.find('img')
                if img:
                    return img.get('src', '')
            except Exception:
                pass
        return ''

    @staticmethod
    def fetch_rss(url, source_name, category, limit=8):
        """Fetch and parse an RSS feed."""
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12)
            if resp.status_code != 200:
                print(f"⚠️  {source_name} [{category}] → HTTP {resp.status_code}")
                return []

            feed = feedparser.parse(resp.content)
            if not feed.entries:
                print(f"⚠️  {source_name} [{category}] → empty feed")
                return []

            items = []
            for entry in feed.entries[:limit]:
                url_link = entry.get('link', '')
                if not url_link:
                    continue

                # Clean description — strip HTML tags
                raw_desc = entry.get('summary', entry.get('description', ''))
                try:
                    desc = BeautifulSoup(raw_desc, 'html.parser').get_text(separator=' ').strip()
                except Exception:
                    desc = raw_desc

                items.append({
                    'title':        entry.get('title', 'Untitled').strip(),
                    'description':  desc[:500],
                    'content':      desc,
                    'url':          url_link,
                    'published_at': entry.get('published', ''),
                    'source':       source_name,
                    'category':     category.upper(),
                    'image_url':    EnhancedNewsFetcher._parse_image(entry),
                })

            print(f"✅ {source_name} [{category}] → {len(items)} articles")
            return items

        except requests.exceptions.Timeout:
            print(f"⏱️  Timeout: {source_name} [{category}]")
            return []
        except Exception as e:
            print(f"❌ {source_name} [{category}] error: {e}")
            return []

    # ── Public fetch methods ──────────────────────────────────────────────────

    @staticmethod
    def fetch_google_nigeria_news(category='news', limit=8):
        """Fetch Nigeria-specific news from Google News RSS (geo-targeted)."""
        url = GOOGLE_NEWS_NIGERIA.get(
            category,
            'https://news.google.com/rss/search?q=Nigeria&hl=en-NG&gl=NG&ceid=NG:en'
        )
        return EnhancedNewsFetcher.fetch_rss(url, 'Google News Nigeria', category, limit)

    @staticmethod
    def fetch_google_news_by_category(category='news', limit=8):
        """Fetch global topic news from Google News, geo-set to Nigeria."""
        url = GOOGLE_NEWS_GLOBAL.get(
            category,
            'https://news.google.com/rss?hl=en-NG&gl=NG&ceid=NG:en'
        )
        return EnhancedNewsFetcher.fetch_rss(url, 'Google News', category, limit)

    @staticmethod
    def fetch_nigerian_rss(outlet='punch', category='news', limit=8):
        """Fetch from a specific Nigerian news outlet RSS."""
        outlet_display = {
            'punch': 'Punch Nigeria', 'vanguard': 'Vanguard Nigeria',
            'channels': 'Channels TV', 'thisday': 'ThisDay Live',
            'guardian_ng': 'Guardian Nigeria', 'thecable': 'The Cable',
            'premiumtimes': 'Premium Times',
        }
        feeds = NIGERIAN_RSS.get(outlet, {})
        url = feeds.get(category) or feeds.get('news')
        if not url:
            return []
        return EnhancedNewsFetcher.fetch_rss(url, outlet_display.get(outlet, outlet), category, limit)

    @staticmethod
    def fetch_bbc_rss(category='news', limit=8):
        url = BBC_RSS.get(category, BBC_RSS['news'])
        return EnhancedNewsFetcher.fetch_rss(url, 'BBC News', category, limit)

    @staticmethod
    def fetch_news_api(category='general', country='ng', limit=10):
        """Fetch from NewsAPI (requires NEWS_API_KEY in settings)."""
        api_key = getattr(settings, 'NEWS_API_KEY', os.environ.get('NEWS_API_KEY', ''))
        if not api_key:
            return []
        try:
            r = requests.get("https://newsapi.org/v2/top-headlines", timeout=10, params={
                'apiKey': api_key, 'category': category,
                'country': country, 'pageSize': limit, 'language': 'en',
            })
            if r.status_code == 200:
                return [{
                    'title':        a.get('title', 'Untitled'),
                    'description':  a.get('description', ''),
                    'content':      a.get('content', ''),
                    'url':          a.get('url', ''),
                    'image_url':    a.get('urlToImage', ''),
                    'published_at': a.get('publishedAt', ''),
                    'source':       a.get('source', {}).get('name', 'NewsAPI'),
                    'category':     category.upper(),
                } for a in r.json().get('articles', []) if a.get('url')]
        except Exception as e:
            print(f"❌ NewsAPI error: {e}")
        return []

    # ── Main fetch orchestrator ───────────────────────────────────────────────

    @staticmethod
    def fetch_latest_nigerian_news(limit_per_source=6):
        """
        Priority fetch: latest Nigerian news from all available sources.
        This is the MAIN method called by the scheduler and dashboard button.
        Returns deduplicated articles sorted by source priority.
        """
        all_articles = []
        seen_urls = set()
        seen_titles = set()

        def add_articles(articles):
            for a in articles:
                url   = a.get('url', '').strip()
                title = a.get('title', '').strip().lower()[:80]
                if not url or url in seen_urls:
                    continue
                if title and title in seen_titles:
                    continue
                seen_urls.add(url)
                seen_titles.add(title)
                all_articles.append(a)

        categories = ['news', 'politics', 'economy', 'entertainment', 'sport', 'technology']

        # ── Priority 1: Google News Nigeria (best for latest) ──
        print("\n📡 Fetching Google News Nigeria...")
        for cat in categories:
            add_articles(EnhancedNewsFetcher.fetch_google_nigeria_news(cat, limit_per_source))
            time.sleep(0.3)

        # ── Priority 2: Google News global topics (geo=NG) ──
        print("\n📡 Fetching Google News (global topics, NG locale)...")
        for cat in categories:
            add_articles(EnhancedNewsFetcher.fetch_google_news_by_category(cat, limit_per_source))
            time.sleep(0.3)

        # ── Priority 3: Nigerian RSS outlets ──
        print("\n📡 Fetching Nigerian RSS outlets...")
        for outlet in ['punch', 'vanguard', 'channels', 'premiumtimes', 'thecable', 'guardian_ng', 'thisday']:
            for cat in ['news', 'politics', 'economy', 'entertainment', 'sport']:
                add_articles(EnhancedNewsFetcher.fetch_nigerian_rss(outlet, cat, limit_per_source))
                time.sleep(0.2)

        # ── Priority 4: BBC for international context ──
        print("\n📡 Fetching BBC News...")
        for cat in ['news', 'economy', 'technology']:
            add_articles(EnhancedNewsFetcher.fetch_bbc_rss(cat, limit_per_source))
            time.sleep(0.2)

        print(f"\n🎉 Total unique articles: {len(all_articles)}")
        return all_articles

    @staticmethod
    def fetch_multiple_sources(categories=None, sources=None, limit_per_source=5):
        """
        Flexible fetch — used by dashboard manual button and API endpoints.
        Defaults to Nigerian-first fetch if no sources specified.
        """
        # If called with defaults, use the smarter Nigerian-first fetcher
        nigerian_outlets = {'punch', 'vanguard', 'channels', 'thisday', 'guardian_ng', 'thecable', 'premiumtimes'}

        if categories is None:
            categories = ['news', 'sport', 'entertainment', 'economy', 'politics', 'technology']
        if sources is None:
            return EnhancedNewsFetcher.fetch_latest_nigerian_news(limit_per_source)

        all_articles = []
        seen_urls = set()

        def add(articles):
            for a in articles:
                if a.get('url') and a['url'] not in seen_urls:
                    seen_urls.add(a['url'])
                    all_articles.append(a)

        for source in sources:
            for category in categories:
                print(f"📡 {source} [{category}]")
                if source == 'google_nigeria':
                    add(EnhancedNewsFetcher.fetch_google_nigeria_news(category, limit_per_source))
                elif source == 'google':
                    add(EnhancedNewsFetcher.fetch_google_news_by_category(category, limit_per_source))
                elif source in nigerian_outlets:
                    add(EnhancedNewsFetcher.fetch_nigerian_rss(source, category, limit_per_source))
                elif source == 'bbc':
                    add(EnhancedNewsFetcher.fetch_bbc_rss(category, limit_per_source))
                elif source == 'newsapi':
                    cat_map = {'news': 'general', 'sport': 'sports', 'entertainment': 'entertainment',
                               'economy': 'business', 'politics': 'general', 'technology': 'technology'}
                    add(EnhancedNewsFetcher.fetch_news_api(cat_map.get(category, 'general'), limit=limit_per_source))
                time.sleep(0.3)

        print(f"🎉 Total: {len(all_articles)} articles")
        return all_articles

    # ── Post generation ───────────────────────────────────────────────────────

    @staticmethod
    def generate_blog_post_from_article(article):
        """Convert a fetched news article into a blog Post."""
        from django.utils.text import slugify
        from django.contrib.auth.models import User
        from blog.models import Category, Post

        try:
            cat_name = article.get('category', 'NEWS').upper()
            # Normalise category name
            cat_map = {
                'SPORT': 'SPORT', 'SPORTS': 'SPORT',
                'ECONOMY': 'ECONOMY', 'BUSINESS': 'ECONOMY',
                'ENTERTAINMENT': 'ENTERTAINMENT',
                'POLITICS': 'POLITICS',
                'TECHNOLOGY': 'TECHNOLOGY',
                'NEWS': 'NEWS',
            }
            cat_name = cat_map.get(cat_name, cat_name)
            category_obj, _ = Category.objects.get_or_create(name=cat_name)

            try:
                author = User.objects.get(username='admin')
            except User.DoesNotExist:
                author = User.objects.first()
            if not author:
                print("❌ No user found to assign as author")
                return None

            title = article.get('title', 'Untitled').replace('[News] ', '').strip()

            # Slug
            base_slug = slugify(title[:80])
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            desc    = article.get('description', '') or article.get('content', '')
            content_body = article.get('content', '') or desc
            source  = article.get('source', 'Unknown')
            orig_url = article.get('url', '#')

            content = f"""
<div class="article-body">
  <p class="lead">{desc}</p>

  <div>{content_body[:3000]}</div>

  <hr>
  <div class="alert alert-light border-start border-danger border-3 mt-4" style="font-size:.85rem;">
    <strong>Source:</strong> {source}&nbsp;&nbsp;
    <a href="{orig_url}" target="_blank" rel="noopener" class="btn btn-sm btn-outline-danger ms-2">
      Read original article →
    </a>
  </div>
</div>
"""

            post = Post.objects.create(
                title=title[:499],
                slug=slug,
                content=content,
                excerpt=(desc[:300] or title[:300]),
                author=author,
                category=category_obj,
                featured_image=article.get('image_url', ''),
                published_date=timezone.now(),
            )
            post.tags.add('news', source.lower().split()[0], cat_name.lower())
            print(f"✅ Created post: {post.title[:60]}")
            return post

        except Exception as e:
            print(f"❌ Error generating post: {e}")
            import traceback; traceback.print_exc()
            return None

    @staticmethod
    def extract_content_from_url(url):
        """Scrape full article text from a URL."""
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.content, 'html.parser')
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            return ' '.join(soup.get_text(separator=' ').split())[:5000]
        except Exception as e:
            print(f"❌ Content extract error: {e}")
            return None


# ── Backward-compatible wrapper ───────────────────────────────────────────────

class SimpleNewsFetcher:

    @staticmethod
    def fetch_google_news_rss():
        nigerian = EnhancedNewsFetcher.fetch_google_nigeria_news('news', 8)
        global_  = EnhancedNewsFetcher.fetch_google_news_by_category('news', 5)
        punch    = EnhancedNewsFetcher.fetch_nigerian_rss('punch', 'news', 5)
        vanguard = EnhancedNewsFetcher.fetch_nigerian_rss('vanguard', 'news', 5)
        return nigerian + global_ + punch + vanguard

    @staticmethod
    def fetch_reddit_news(subreddit='news', limit=10):
        return []  # Reddit is unreliable, removed

    @staticmethod
    def fetch_newsapi():
        return EnhancedNewsFetcher.fetch_news_api('general', 'ng', 10)

    @staticmethod
    def categorize_article(title, description):
        text = (title + ' ' + description).lower()
        categories = {
            'ENTERTAINMENT': ['movie', 'film', 'actor', 'actress', 'celebrity', 'music', 'show', 'nollywood', 'afrobeats', 'wizkid', 'davido', 'burna'],
            'SPORT':         ['sport', 'football', 'basketball', 'soccer', 'super eagles', 'afcon', 'premier league', 'npfl', 'score', 'goal'],
            'POLITICS':      ['government', 'president', 'minister', 'election', 'vote', 'party', 'senate', 'tinubu', 'abuja', 'governor', 'national assembly'],
            'ECONOMY':       ['economy', 'market', 'stock', 'price', 'bank', 'naira', 'cbn', 'inflation', 'oil', 'forex', 'budget', 'dollar'],
            'TECHNOLOGY':    ['technology', 'tech', 'software', 'app', 'digital', 'startup', 'fintech', 'ai', 'internet'],
        }
        scores = {cat: sum(1 for kw in kws if kw in text) for cat, kws in categories.items()}
        best = max(scores, key=scores.get)
        return best if scores[best] >= 2 else 'NEWS'

    @staticmethod
    def generate_summary(text, max_length=150):
        if not text:
            return ''
        if len(text) <= max_length:
            return text
        return text[:max_length].rsplit(' ', 1)[0] + '...'

    @staticmethod
    def extract_content_from_url(url):
        return EnhancedNewsFetcher.extract_content_from_url(url)