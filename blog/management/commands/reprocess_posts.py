from django.core.management.base import BaseCommand
from blog.models import Post
from blog.ai_service import OpenRouterService
import re
import time

class Command(BaseCommand):
    help = 'Reprocess existing posts through AI humanization'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=10,
                            help='Number of posts to reprocess')
        parser.add_argument('--category', type=str, default='',
                            help='Filter by category name')

    def handle(self, *args, **options):
        limit = options['limit']
        category_filter = options['category']

        queryset = Post.objects.all().order_by('-published_date')

        if category_filter:
            queryset = queryset.filter(category__name__iexact=category_filter)

        posts = queryset[:limit]
        service = OpenRouterService()

        if not service.api_key:
            self.stdout.write(self.style.ERROR('❌ No OpenRouter API key found'))
            return

        self.stdout.write(f'🔄 Reprocessing {posts.count()} posts...')
        updated = 0
        failed = 0

        for post in posts:
            try:
                self.stdout.write(f'📝 Processing: {post.title[:60]}...')

                # Skip if content is raw RSS junk
                if '<a href="https://news.google.com' in post.content:
                    self.stdout.write(self.style.WARNING('⚠️  Skipping RSS junk post'))
                    continue

                # Strip existing HTML to get plain text for reprocessing
                plain_text = re.sub(r'<[^>]+>', '', post.content).strip()

                if len(plain_text) < 100:
                    self.stdout.write(self.style.WARNING('⚠️  Content too short, skipping'))
                    continue

                category = post.category.name if post.category else 'NEWS'
                result = service.paraphrase_article(
                    title=post.title,
                    content=plain_text,
                    category=category,
                    min_words=500
                )

                if result['success']:
                    post.content = result['content']
                    post.excerpt = result['summary'][:500]
                    post.save()
                    updated += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'✅ Updated: {post.title[:50]} ({result["word_count"]} words)'
                    ))
                else:
                    failed += 1
                    self.stdout.write(self.style.ERROR(
                        f'❌ Failed: {result.get("error", "Unknown error")}'
                    ))

                # Delay between requests to avoid rate limiting
                time.sleep(3)

            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(
            f'\n🎉 Done. Updated: {updated} | Failed: {failed}'
        ))