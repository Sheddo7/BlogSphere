# setup_enhanced_dashboard.py - FIXED VERSION
import os

print("Setting up enhanced news dashboard...")

# 1. Create the template directory if it doesn't exist
templates_dir = 'templates/blog'
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)
    print(f"Created directory: {templates_dir}")

# 2. Create the enhanced dashboard template WITHOUT emojis
template_content = '''{% extends 'base.html' %}

{% block title %}Enhanced News Dashboard - BlogSphere{% endblock %}

{% block content %}
<div class="container mt-4">
    <h1 class="mb-4">Enhanced News Dashboard</h1>

    <!-- Stats Cards -->
    <div class="row mb-4">
        <div class="col-md-3 mb-3">
            <div class="card bg-primary text-white">
                <div class="card-body">
                    <h5 class="card-title">Total Articles</h5>
                    <h2>{{ stats.total_articles }}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card bg-success text-white">
                <div class="card-body">
                    <h5 class="card-title">Today's Articles</h5>
                    <h2>{{ stats.today_articles }}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card bg-info text-white">
                <div class="card-body">
                    <h5 class="card-title">Auto Posts</h5>
                    <h2>{{ stats.auto_posts }}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="card bg-warning text-white">
                <div class="card-body">
                    <h5 class="card-title">To Process</h5>
                    <h2>{{ stats.to_process }}</h2>
                </div>
            </div>
        </div>
    </div>

    <!-- Quick Actions -->
    <div class="card mb-4">
        <div class="card-header">
            <h4>Quick Actions</h4>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Fetch News Now</h5>
                            <form method="post" action="{% url 'fetch_news_now' %}" id="fetchForm">
                                {% csrf_token %}
                                <div class="mb-3">
                                    <label class="form-label">Categories</label>
                                    <select name="categories" class="form-select" multiple>
                                        <option value="news" selected>News</option>
                                        <option value="sport" selected>Sport</option>
                                        <option value="entertainment" selected>Entertainment</option>
                                        <option value="economy">Economy</option>
                                        <option value="politics">Politics</option>
                                        <option value="technology">Technology</option>
                                    </select>
                                    <small class="form-text text-muted">Hold Ctrl to select multiple</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Sources</label>
                                    <select name="sources" class="form-select" multiple>
                                        <option value="google" selected>Google News</option>
                                        <option value="reddit" selected>Reddit</option>
                                        <option value="bbc" selected>BBC</option>
                                        <option value="newsapi">NewsAPI</option>
                                    </select>
                                </div>
                                <button type="submit" class="btn btn-primary" id="fetchBtn">
                                    <i class="fas fa-sync-alt"></i> Fetch News
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 mb-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Generate Blog Posts</h5>
                            <form method="post" action="{% url 'generate_posts_now' %}" id="generateForm">
                                {% csrf_token %}
                                <div class="mb-3">
                                    <label class="form-label">Number of posts to generate</label>
                                    <input type="number" name="count" class="form-control" value="3" min="1" max="10">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Category filter</label>
                                    <select name="category" class="form-select">
                                        <option value="">All Categories</option>
                                        {% for cat in categories %}
                                        <option value="{{ cat.name }}">{{ cat.name }}</option>
                                        {% endfor %}
                                    </select>
                                </div>
                                <button type="submit" class="btn btn-success" id="generateBtn">
                                    <i class="fas fa-robot"></i> Generate Posts
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Recent Articles -->
    <div class="card">
        <div class="card-header d-flex justify-content-between align-items-center">
            <h4>Recent News Articles</h4>
            <div>
                <a href="{% url 'admin:blog_newsarticle_changelist' %}" class="btn btn-sm btn-primary">
                    <i class="fas fa-list"></i> View All
                </a>
                <a href="{% url 'admin:blog_newsarticle_add' %}" class="btn btn-sm btn-success">
                    <i class="fas fa-plus"></i> Add Manual
                </a>
            </div>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Source</th>
                            <th>Category</th>
                            <th>Published</th>
                            <th>Converted</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for article in recent_articles %}
                        <tr>
                            <td>{{ article.title|truncatechars:60 }}</td>
                            <td><span class="badge bg-secondary">{{ article.source }}</span></td>
                            <td><span class="badge bg-info">{{ article.category }}</span></td>
                            <td>{{ article.published_at|date:"M d, Y"|default:"N/A" }}</td>
                            <td>
                                {% if article.created_as_post %}
                                <span class="badge bg-success">Yes</span>
                                {% else %}
                                <span class="badge bg-warning">No</span>
                                {% endif %}
                            </td>
                            <td>
                                <a href="{{ article.url }}" target="_blank" class="btn btn-sm btn-outline-primary">
                                    <i class="fas fa-external-link-alt"></i>
                                </a>
                                <a href="{% url 'admin:blog_newsarticle_change' article.id %}" class="btn btn-sm btn-outline-secondary">
                                    <i class="fas fa-edit"></i>
                                </a>
                                <button onclick="convertToPost({{ article.id }})" class="btn btn-sm btn-outline-success">
                                    <i class="fas fa-file-alt"></i>
                                </button>
                            </td>
                        </tr>
                        {% empty %}
                        <tr>
                            <td colspan="6" class="text-center">No articles found. Fetch some news!</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script>
    // Fetch news with AJAX
    document.getElementById('fetchForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const form = this;
        const button = form.querySelector('#fetchBtn');
        const originalText = button.innerHTML;

        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Fetching...';
        button.disabled = true;

        fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Success: ' + data.message, 'success');
                setTimeout(() => location.reload(), 2000);
            } else {
                showToast('Error: ' + data.message, 'danger');
            }
        })
        .catch(error => {
            showToast('Error fetching news', 'danger');
        })
        .finally(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        });
    });

    // Generate posts with AJAX
    document.getElementById('generateForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const form = this;
        const button = form.querySelector('#generateBtn');
        const originalText = button.innerHTML;

        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        button.disabled = true;

        fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Success: ' + data.message, 'success');
                setTimeout(() => location.reload(), 2000);
            } else {
                showToast('Error: ' + data.message, 'danger');
            }
        })
        .catch(error => {
            showToast('Error generating posts', 'danger');
        })
        .finally(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        });
    });

    function convertToPost(articleId) {
        fetch('/api/convert-to-post/' + articleId + '/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Success: ' + data.message, 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                showToast('Error: ' + data.message, 'danger');
            }
        })
        .catch(error => {
            showToast('Error converting article', 'danger');
        });
    }

    function showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-' + type + ' border-0 position-fixed bottom-0 end-0 m-3';
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">` + message + `</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        document.body.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        setTimeout(() => toast.remove(), 3000);
    }
</script>
{% endblock %}'''

# Write with UTF-8 encoding to handle any special characters
with open(os.path.join(templates_dir, 'enhanced_news_dashboard.html'), 'w', encoding='utf-8') as f:
    f.write(template_content)
print("Created enhanced_news_dashboard.html")

# 3. Create ai_service.py if it doesn't exist
ai_service_content = '''# blog/ai_service.py - SIMPLIFIED VERSION
import os
import requests
import feedparser
from django.conf import settings
from django.utils import timezone

class EnhancedNewsFetcher:
    """Enhanced news fetcher with multiple sources"""

    @staticmethod
    def fetch_news_api(category='general', limit=10):
        """Fetch news from NewsAPI"""
        api_key = getattr(settings, 'NEWS_API_KEY', os.environ.get('NEWS_API_KEY', ''))

        if not api_key:
            print("Warning: NewsAPI key not found")
            return []

        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'apiKey': api_key,
                'category': category,
                'country': 'us',
                'pageSize': limit,
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
        except Exception as e:
            print(f"Error fetching NewsAPI: {e}")
        return []

    @staticmethod
    def fetch_google_news_by_category(category='news', limit=10):
        """Fetch news from Google News"""
        try:
            feed_url = "https://news.google.com/rss"
            feed = feedparser.parse(feed_url)
            news_items = []

            for entry in feed.entries[:limit]:
                news_items.append({
                    'title': entry.title,
                    'description': entry.get('summary', ''),
                    'content': entry.get('summary', ''),
                    'url': entry.link,
                    'published_at': entry.get('published', ''),
                    'source': entry.get('source', {}).get('title', 'Google News'),
                    'category': category.upper(),
                })
            return news_items
        except Exception as e:
            print(f"Error fetching Google News: {e}")
            return []

    @staticmethod
    def fetch_multiple_sources(categories=None, sources=None, limit_per_source=3):
        """Fetch news from multiple sources"""
        if categories is None:
            categories = ['news', 'sport', 'entertainment']

        if sources is None:
            sources = ['google', 'newsapi']

        all_articles = []

        for source in sources:
            for category in categories:
                print(f"Fetching {category} from {source}...")

                if source == 'google':
                    articles = EnhancedNewsFetcher.fetch_google_news_by_category(category, limit_per_source)
                elif source == 'newsapi':
                    articles = EnhancedNewsFetcher.fetch_news_api(category, limit_per_source)
                else:
                    continue

                if articles:
                    all_articles.extend(articles)

        return all_articles

    @staticmethod
    def generate_blog_post_from_article(article):
        """Generate a blog post from a news article"""
        from django.utils.text import slugify
        from django.contrib.auth.models import User
        from blog.models import Category, Post

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

            # Create blog post
            post = Post.objects.create(
                title=f"[News] {article['title'][:100]}",
                slug=slug,
                content=article.get('description', article.get('content', '')),
                excerpt=article.get('description', '')[:200],
                author=author,
                category=category_obj,
                published_date=timezone.now(),
            )

            # Add tags
            post.tags.add('news', 'auto-generated')

            return post

        except Exception as e:
            print(f"Error generating blog post: {e}")
            return None'''

if not os.path.exists('blog/ai_service.py'):
    with open('blog/ai_service.py', 'w', encoding='utf-8') as f:
        f.write(ai_service_content)
    print("Created ai_service.py")

# 4. Update settings.py with NEWS_API_KEY
settings_file = 'blog_core/settings.py'
if os.path.exists(settings_file):
    with open(settings_file, 'r', encoding='utf-8') as f:
        settings_content = f.read()

    # Add NEWS_API_KEY if not present
    if 'NEWS_API_KEY' not in settings_content:
        # Find a good place to add it (after other settings)
        lines = settings_content.split('\n')
        for i, line in enumerate(lines):
            if 'SECRET_KEY' in line:
                # Add after SECRET_KEY
                lines.insert(i + 1, "NEWS_API_KEY = ''  # Add your NewsAPI key here")
                break

        with open(settings_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print("Added NEWS_API_KEY placeholder to settings.py")

print("\nSetup complete!")
print("\nNext steps:")
print("1. Add your NewsAPI key to settings.py or environment")
print("2. Run: python manage.py runserver")
print("3. Visit: http://localhost:8000/enhanced-news-dashboard/")
print("4. Login as admin to access the dashboard")