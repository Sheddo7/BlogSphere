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

    # Dashboards
    path('dashboard/', views.combined_dashboard, name='combined_dashboard'),

    # API endpoints
    path('api/fetch-news-now/', views.fetch_news_now, name='fetch_news_now'),
    path('api/get-draft/<int:draft_id>/', views.get_draft, name='get_draft'),
    path('api/update-draft/', views.update_draft, name='update_draft'),
    path('api/publish-draft/', views.publish_draft, name='publish_draft'),
    path('api/delete-draft/<int:draft_id>/', views.delete_draft, name='delete_draft'),
    path('api/post-article/', views.post_article, name='post_article'),
    path('api/post-multiple-articles/', views.post_multiple_articles, name='post_multiple_articles'),
    path('api/get-post/<int:post_id>/', views.get_post, name='get_post'),
    path('api/update-post-image/', views.update_post_image, name='update_post_image'),
    path('api/remove-post-image/<int:post_id>/', views.remove_post_image, name='remove_post_image'),
    path('api/delete-news-article/<int:article_id>/', views.delete_news_article, name='delete_news_article'),
    path('api/delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('api/openrouter-chat/', views.openrouter_chat, name='openrouter_chat'),
    path('api/preview-article/', views.preview_article, name='preview_article'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)