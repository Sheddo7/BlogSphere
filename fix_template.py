# fix_template.py
import os

print("🔧 Fixing template structure...")

# 1. Create directories if they don't exist
templates_dir = 'templates'
blog_templates_dir = os.path.join(templates_dir, 'blog')

if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)
    print(f"✅ Created: {templates_dir}")

if not os.path.exists(blog_templates_dir):
    os.makedirs(blog_templates_dir)
    print(f"✅ Created: {blog_templates_dir}")

# 2. Create the enhanced news dashboard template
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

# Write the template file
template_path = os.path.join(blog_templates_dir, 'enhanced_news_dashboard.html')
with open(template_path, 'w', encoding='utf-8') as f:
    f.write(template_content)
print(f"✅ Created: {template_path}")

# 3. Check your settings.py template configuration
print("\n📋 Checking your template configuration...")
settings_file = 'blog_core/settings.py'
if os.path.exists(settings_file):
    with open(settings_file, 'r', encoding='utf-8') as f:
        settings_content = f.read()

    # Check if TEMPLATES configuration is correct
    if 'TEMPLATES' in settings_content:
        print("✅ TEMPLATES configuration found")

        # Check template directories
        if 'DIRS' in settings_content and 'templates' in settings_content:
            print("✅ Template DIRS configuration looks good")
        else:
            print("⚠️  Check TEMPLATES['DIRS'] in settings.py")
            print("   It should include: BASE_DIR / 'templates'")

    # Check if INSTALLED_APPS includes django.contrib.staticfiles
    if "'django.contrib.staticfiles'" in settings_content:
        print("✅ django.contrib.staticfiles is installed")
    else:
        print("❌ django.contrib.staticfiles might be missing from INSTALLED_APPS")

print("\n🎉 Template fix complete!")
print("\n📋 Next steps:")
print("1. Check if the template file exists:")
print(f"   {os.path.abspath(template_path)}")
print("\n2. Restart the server:")
print("   python manage.py runserver")
print("\n3. Visit: http://localhost:8000/enhanced-news-dashboard/")
print("   (Login as admin required)")