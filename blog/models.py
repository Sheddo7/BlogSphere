# blog/models.py - ORIGINAL COMPLETE VERSION
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.utils import timezone
from taggit.managers import TaggableManager
import random

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    excerpt = models.CharField(max_length=300)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    featured_image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    views = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    tags = TaggableManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_date = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = base_slug
            counter = 1
            while Post.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_date']

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"

class NewsSource(models.Model):
    name = models.CharField(max_length=100)
    api_endpoint = models.URLField()
    api_key = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    update_frequency = models.IntegerField(default=60)

    def __str__(self):
        return self.name

class NewsArticle(models.Model):
    title = models.CharField(max_length=500)
    content = models.TextField()
    summary = models.TextField(blank=True)
    url = models.URLField(unique=True)
    source = models.CharField(max_length=100)
    category = models.CharField(max_length=50, blank=True)
    image_url = models.URLField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)
    created_as_post = models.BooleanField(default=False)

    class Meta:
        ordering = ['-published_at', '-imported_at']

    def __str__(self):
        return self.title[:100]

    def save(self, *args, **kwargs):
        if not self.summary and self.content:
            self.summary = self.content[:200] + '...'
        super().save(*args, **kwargs)