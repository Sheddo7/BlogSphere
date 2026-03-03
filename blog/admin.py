# blog/admin.py - UPDATED VERSION (remove print statements)
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Post, Comment, NewsArticle

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Posts'

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'published_date', 'is_featured', 'views']
    list_filter = ['category', 'is_featured', 'published_date', 'author']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'
    list_per_page = 20

    fieldsets = (
        ('Main Content', {
            'fields': ('title', 'slug', 'content', 'excerpt')
        }),
        ('Author & Category', {
            'fields': ('author', 'category', 'tags')
        }),
        ('Featured Content', {
            'fields': ('featured_image', 'is_featured')
        }),
        ('Publishing', {
            'fields': ('published_date',)
        }),
    )

    readonly_fields = ('views', 'created_at', 'updated_at')
    actions = ['make_featured', 'remove_featured']

    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} posts marked as featured.")
    make_featured.short_description = "Mark as featured"

    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"{updated} posts removed from featured.")
    remove_featured.short_description = "Remove from featured"

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'post', 'created_at', 'is_approved']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['name', 'email', 'content']
    actions = ['approve_comments', 'disapprove_comments']

    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} comments approved.")
    approve_comments.short_description = "Approve comments"

    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} comments disapproved.")
    disapprove_comments.short_description = "Disapprove comments"

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'source', 'category', 'published_at', 'created_as_post']
    list_filter = ['source', 'category', 'created_as_post']
    search_fields = ['title', 'content', 'summary']
    readonly_fields = ['imported_at']
    actions = ['create_posts_from_selected']

    fieldsets = (
        ('Article Info', {
            'fields': ('title', 'content', 'summary', 'url')
        }),
        ('Source Info', {
            'fields': ('source', 'category', 'image_url', 'published_at')
        }),
        ('Status', {
            'fields': ('created_as_post', 'imported_at')
        }),
    )

    def create_posts_from_selected(self, request, queryset):
        from django.contrib.auth.models import User
        from django.utils.text import slugify
        from django.utils import timezone

        created_count = 0
        for article in queryset:
            if not article.created_as_post:
                try:
                    author = User.objects.get(username='admin')
                except User.DoesNotExist:
                    author = User.objects.first()

                base_slug = slugify(article.title)
                slug = base_slug
                counter = 1
                while Post.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                Post.objects.create(
                    title=article.title,
                    slug=slug,
                    content=article.content,
                    excerpt=article.summary[:200],
                    author=author,
                    category=Category.objects.filter(name=article.category).first() or Category.objects.first(),
                    featured_image=article.image_url or '',
                    published_date=article.published_at or timezone.now(),
                )

                article.created_as_post = True
                article.save()
                created_count += 1

        self.message_user(request, f"Created {created_count} blog posts from selected articles.")
    create_posts_from_selected.short_description = "Create blog posts from selected articles"

# REMOVED: print("✅ Admin panel ready!")
# REMOVED: print("👉 Visit: http://localhost:8000/admin/")
