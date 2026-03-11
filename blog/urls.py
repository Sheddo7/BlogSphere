# blog/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='blog-home'),
    path('post/<slug:slug>/', views.post_detail, name='post-detail'),
    path('category/<slug:slug>/', views.category_posts, name='category-posts'),
    path('search/', views.search, name='search'),
    path('news-dashboard/', views.news_dashboard, name='news-dashboard'),
    path('enhanced-news-dashboard/', views.enhanced_news_dashboard, name='enhanced-news-dashboard'),
    path('fetch-news/', views.fetch_news_now, name='fetch-news'),
    path('generate-posts/', views.generate_posts_now, name='generate-posts'),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard-stats'),
    path('convert-to-post/<int:article_id>/', views.convert_to_post, name='convert-to-post'),
    path('post-article/', views.post_article, name='post-article'),
    path('post-multiple/', views.post_multiple_articles, name='post-multiple'),
    path('get-post/<int:post_id>/', views.get_post, name='get-post'),
    path('update-post-image/', views.update_post_image, name='update-post-image'),
    path('remove-post-image/<int:post_id>/', views.remove_post_image, name='remove-post-image'),
    path('delete-news-article/<int:article_id>/', views.delete_news_article, name='delete-news-article'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete-post'),
    path('debug-feeds/', views.debug_nigerian_feeds, name='debug-feeds'),  # <-- ADD THIS
]