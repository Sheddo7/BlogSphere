from django import template
from blog.models import Post
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.simple_tag
def get_trending_posts(count=5, days=None):
    """
    Returns top 'count' posts by views, optionally filtered by last 'days'.
    Usage: {% get_trending_posts 5 days=7 as trending_list %}
    """
    queryset = Post.objects.all()
    if days:
        date_limit = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(published_date__gte=date_limit)
    return queryset.order_by('-views')[:count]