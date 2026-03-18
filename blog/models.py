# blog/models.py
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.utils import timezone
from taggit.managers import TaggableManager


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
    title = models.CharField(max_length=500)  # was 200 — titles from news can be long
    slug = models.SlugField(unique=True, blank=True, max_length=550)
    content = models.TextField()
    excerpt = models.CharField(max_length=500, blank=True)  # was 300
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    featured_image = models.ImageField(
        upload_to='blog_images/',
        blank=True, null=True,
        max_length=1000
    )
    image_url = models.URLField(
        blank=True, default='',
        max_length=1000,
        help_text='External image URL from news sources'
    )
    views = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    tags = TaggableManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_date = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:500]
            self.slug = base_slug
            counter = 1
            while Post.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_image_url(self):
        if self.featured_image:
            return self.featured_image.url
        if self.image_url:
            return self.image_url
        return ''

    class Meta:
        ordering = ['-published_date']


# Comment model has been removed


class NewsSource(models.Model):
    name = models.CharField(max_length=100)
    api_endpoint = models.URLField()
    api_key = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    update_frequency = models.IntegerField(default=60)

    def __str__(self):
        return self.name


class NewsArticle(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft - Ready to Edit'),
        ('ready', 'Ready to Publish'),
        ('published', 'Published to Blog'),
    ]

    title = models.CharField(max_length=500)
    content = models.TextField()
    summary = models.TextField(blank=True)
    url = models.URLField(unique=True, max_length=1000)
    source = models.CharField(max_length=100)
    category = models.CharField(max_length=50, blank=True)
    image_url = models.URLField(blank=True, max_length=1000)
    published_at = models.DateTimeField(null=True, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)
    created_as_post = models.BooleanField(default=False)

    # DRAFT WORKFLOW FIELDS
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    word_count = models.IntegerField(default=0)
    ai_processed = models.BooleanField(default=False)
    tags = models.CharField(max_length=500, blank=True, default='news')
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['-imported_at']

    def __str__(self):
        return self.title[:100]

    def save(self, *args, **kwargs):
        if not self.summary and self.content:
            self.summary = self.content[:200] + '...'
        if not self.word_count and self.content:
            self.word_count = len(self.content.split())
        super().save(*args, **kwargs)