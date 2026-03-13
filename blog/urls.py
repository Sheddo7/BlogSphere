# blog/urls.py - COMPLETE UPDATED VERSION
from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = [
    # Basic URLs
    path(settings.ADMIN_URL, admin.site.urls),
    path('', views.home, name='home'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('category/<slug:slug>/', views.category_posts, name='category_posts'),
    path('search/', views.search, name='search'),
    path('news-dashboard/', views.news_dashboard, name='news_dashboard'),
    path('api/openrouter-chat/', views.openrouter_chat, name='openrouter_chat'),

    # Enhanced news dashboard URLs
    path('enhanced-news-dashboard/', views.enhanced_news_dashboard, name='enhanced_news_dashboard'),
    path('api/fetch-news-now/', views.fetch_news_now, name='fetch_news_now'),
    path('api/generate-posts-now/', views.generate_posts_now, name='generate_posts_now'),
    path('api/dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
    path('api/convert-to-post/<int:article_id>/', views.convert_to_post, name='convert_to_post'),

    # New API endpoints for enhanced dashboard
    path('api/post-article/', views.post_article, name='post_article'),
    path('api/post-multiple-articles/', views.post_multiple_articles, name='post_multiple_articles'),
    path('api/get-post/<int:post_id>/', views.get_post, name='get_post'),
    path('api/update-post-image/', views.update_post_image, name='update_post_image'),
    path('api/remove-post-image/<int:post_id>/', views.remove_post_image, name='remove_post_image'),
    path('api/delete-news-article/<int:article_id>/', views.delete_news_article, name='delete_news_article'),
    path('api/delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('dashboard/', views.combined_dashboard, name='combined_dashboard'),
]

handler404 = 'blog.views.custom_404'

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, these should be served by your web server
    pass