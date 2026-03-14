# blog/management/commands/cleanup_categories.py
"""
Django management command to clean up categories and tags
Run this with: python manage.py cleanup_categories
"""

from django.core.management.base import BaseCommand
from blog.models import Post, Category
from taggit.models import Tag


class Command(BaseCommand):
    help = 'Clean up duplicate categories and unwanted tags'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('🧹 Starting cleanup...\n'))

        # 1. Merge "sports" into "sport"
        try:
            sports_category = Category.objects.get(name__iexact='sports')
            sport_category, created = Category.objects.get_or_create(
                name='SPORT',
                defaults={'slug': 'sport'}
            )

            # Move all posts from "sports" to "sport"
            posts_updated = Post.objects.filter(category=sports_category).update(category=sport_category)

            # Delete the duplicate
            sports_category.delete()

            self.stdout.write(self.style.SUCCESS(
                f'✅ Merged "sports" into "sport" ({posts_updated} posts updated)'
            ))
        except Category.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️  No "sports" category found'))

        # 2. Remove "general" category
        try:
            general_category = Category.objects.get(name__iexact='general')

            # Move posts to "NEWS" category
            news_category, created = Category.objects.get_or_create(
                name='NEWS',
                defaults={'slug': 'news'}
            )

            posts_updated = Post.objects.filter(category=general_category).update(category=news_category)
            general_category.delete()

            self.stdout.write(self.style.SUCCESS(
                f'✅ Removed "general" category ({posts_updated} posts moved to NEWS)'
            ))
        except Category.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️  No "general" category found'))

        # 3. Remove "ai-rewritten" tag from all posts
        try:
            ai_tag = Tag.objects.get(name='ai-rewritten')

            # Remove from all posts
            count = 0
            for post in Post.objects.filter(tags__name='ai-rewritten'):
                post.tags.remove(ai_tag)
                count += 1

            # Delete the tag
            ai_tag.delete()

            self.stdout.write(self.style.SUCCESS(
                f'✅ Removed "ai-rewritten" tag from {count} posts'
            ))
        except Tag.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️  No "ai-rewritten" tag found'))

        # 4. Standardize remaining category names
        category_map = {
            'news': 'NEWS',
            'sport': 'SPORT',
            'sports': 'SPORT',
            'entertainment': 'ENTERTAINMENT',
            'economy': 'ECONOMY',
            'business': 'ECONOMY',
            'politics': 'POLITICS',
            'technology': 'TECHNOLOGY',
            'tech': 'TECHNOLOGY'
        }

        for old_name, new_name in category_map.items():
            try:
                old_cat = Category.objects.get(name__iexact=old_name)
                if old_cat.name != new_name:
                    # Get or create the standardized category
                    new_cat, created = Category.objects.get_or_create(
                        name=new_name,
                        defaults={'slug': new_name.lower()}
                    )

                    # Move posts
                    if old_cat.id != new_cat.id:
                        posts_updated = Post.objects.filter(category=old_cat).update(category=new_cat)
                        old_cat.delete()
                        self.stdout.write(self.style.SUCCESS(
                            f'✅ Standardized "{old_name}" → "{new_name}" ({posts_updated} posts)'
                        ))
            except Category.DoesNotExist:
                pass

        # 5. Show final category list
        self.stdout.write(self.style.SUCCESS('\n📊 Final Categories:'))
        for category in Category.objects.all().order_by('name'):
            post_count = category.posts.count()
            self.stdout.write(f'   - {category.name} ({post_count} posts)')

        self.stdout.write(self.style.SUCCESS('\n✨ Cleanup complete!\n'))