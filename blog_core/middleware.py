# blog_core/middleware.py - CREATE THIS FILE

from django.utils.cache import add_never_cache_headers, patch_cache_control


class SecurityHeadersMiddleware:
    """
    Add security and performance headers to all responses
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Performance headers for static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            # Cache static files for 1 year
            patch_cache_control(response, max_age=31536000, public=True, immutable=True)
        elif request.path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico')):
            # Cache images for 1 month
            patch_cache_control(response, max_age=2592000, public=True)
        elif request.path.endswith(('.css', '.js')):
            # Cache CSS/JS for 1 week
            patch_cache_control(response, max_age=604800, public=True)
        else:
            # HTML pages - cache for 5 minutes but allow revalidation
            patch_cache_control(response, max_age=300, public=True, must_revalidate=True)

        return response


class CompressionMiddleware:
    """
    Ensure gzip compression is enabled
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add Vary header for compression
        if 'Vary' in response:
            if 'Accept-Encoding' not in response['Vary']:
                response['Vary'] += ', Accept-Encoding'
        else:
            response['Vary'] = 'Accept-Encoding'

        return response