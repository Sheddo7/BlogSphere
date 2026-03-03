# blog/management/commands/populate_blog.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from blog.models import Post, Category
from django.utils import timezone
import random
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Populates the blog with test data'

    def handle(self, *args, **kwargs):
        # First, ensure we have a user
        if not User.objects.exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user'))

        # Create test categories
        category_names = ['ENTERTAINMENT', 'NEWS', 'POLITICS', 'SPORT', 'VIRAL GIST', 'ECONOMY']

        for cat_name in category_names:
            Category.objects.get_or_create(name=cat_name)
            self.stdout.write(self.style.SUCCESS(f'Created/Found category: {cat_name}'))

        categories = list(Category.objects.all())

        # Create more unique titles
        titles = [
            "She protected you - Artist slams colleague over relationship saga",
            "Empty barrels make the loudest noise - Governor reacts to criticism",
            "I've been single for over 1 year now - Celebrity opens up on split",
            "Algeria defender rejects referee blame, insists opponents have great players",
            "CAF hails goal tribute to superfan during international tournament",
            "Why I didn't attend family burial - Veteran actor explains",
            "Federal government implements new policy on education costs",
            "UK-born teen seeks help to find long-lost Nigerian father",
            "79-year-old multimillionaire seeks young woman to bear him a son",
            "It's an insult to compare musician to legend - Artist rants",
            "Nigerian stock market hits record high amid economic reforms",
            "Local football team secures championship after dramatic final",
            "New tech startup raises millions in funding round",
            "Health ministry announces new vaccination campaign",
            "Environmental activists protest against deforestation project",
            "Celebrity couple announces surprise wedding in private ceremony",
            "Controversial bill passes through parliament after heated debate",
            "Tourist arrivals increase by 30% following marketing campaign",
            "Renowned author releases highly anticipated sequel novel",
            "Scientists discover new species in remote rainforest"
        ]

        contents = [
            "In a recent development that has captivated entertainment circles, a popular artist has publicly criticized a colleague over an ongoing relationship controversy.",
            "Political tensions continue to rise as officials exchange sharp words over development projects in the region.",
            "Breaking his silence on the matter, the celebrity revealed personal details about his relationship status during an exclusive interview.",
            "Sports analysts are reevaluating their predictions following a surprising statement from the international defender.",
            "The football governing body has officially acknowledged a player's heartfelt goal celebration during the tournament.",
            "Family matters take center stage as the veteran actor provides context for his absence from the emotional ceremony.",
            "Educational stakeholders are reviewing new federal guidelines aimed at making learning more affordable nationwide.",
            "An international search has begun as the teenager appeals for public assistance in locating biological family members.",
            "Wealth and age disparities are being discussed after the businessman's unusual public request went viral online.",
            "Cultural appropriation debates resurface as the musician defends artistic legacy against comparisons.",
            "Economic indicators show positive growth following recent policy implementations and market reforms.",
            "Local sports fans celebrate as their team secures a historic victory in the championship finals.",
            "The technology sector continues to expand with another successful funding round for innovative startups.",
            "Public health officials have launched a comprehensive campaign to increase vaccination rates across regions.",
            "Environmental concerns escalate as activists mobilize against planned development in protected areas.",
            "Entertainment news buzzes with the unexpected announcement of a high-profile celebrity wedding.",
            "Legislative proceedings reach a climax as the controversial bill moves forward despite opposition.",
            "Tourism officials report significant growth in visitor numbers following successful international campaigns.",
            "Literary circles eagerly await the release of the acclaimed author's latest work in the series.",
            "Biological researchers announce exciting findings from their expedition in previously unexplored territory."
        ]

        author = User.objects.first()

        for i in range(20):
            title = titles[i % len(titles)]
            content = "<p>" + contents[i % len(contents)] + "</p>" * 5
            excerpt = f"This is a test excerpt for post number {i+1}. The article discusses important developments in the category..."

            post = Post(
                title=title,
                content=content,
                excerpt=excerpt,
                author=author,
                category=random.choice(categories),
                views=random.randint(100, 5000),
                is_featured=random.choice([True, False]),
                published_date=timezone.now()
            )

            # Save will generate unique slug automatically
            post.save()

            # Add tags
            post.tags.add('news', 'latest', 'trending', 'test')
            if i % 3 == 0:
                post.tags.add('exclusive')
            if i % 4 == 0:
                post.tags.add('viral')
            if i % 5 == 0:
                post.tags.add('breaking')

            self.stdout.write(self.style.SUCCESS(f'Created post {i+1}: {post.title} (slug: {post.slug})'))

        self.stdout.write(self.style.SUCCESS('Successfully populated blog with test data!'))
        self.stdout.write(self.style.SUCCESS(f'Total posts: {Post.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Total categories: {Category.objects.count()}'))