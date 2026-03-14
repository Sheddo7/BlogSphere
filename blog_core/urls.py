# blog_core/urls.py - ORIGINAL VERSION
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# ADD THESE IMPORTS:
from blog import views  # ← ADD THIS LINE HERE
from django.contrib.sitemaps.views import sitemap
from blog.sitemaps import PostSitemap, CategorySitemap, StaticViewSitemap
from django.views.generic import TemplateView


# Sitemap configuration
sitemaps = {
    'posts': PostSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('', include('blog.urls')),
    path('accounts/', include('accounts.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
