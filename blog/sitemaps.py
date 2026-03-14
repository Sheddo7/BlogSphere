# blog/sitemaps.py - CREATE THIS NEW FILE

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from blog.models import Post, Category


class PostSitemap(Sitemap):
    """Sitemap for blog posts"""
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Post.objects.all().order_by('-published_date')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f'/post/{obj.slug}/'


class CategorySitemap(Sitemap):
    """Sitemap for categories"""
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return f'/category/{obj.slug}/'


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return ['home', 'about', 'contact', 'privacy_policy', 'terms_of_service']

    def location(self, item):
        return reverse(item)