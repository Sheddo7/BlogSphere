# blog/templatetags/image_helpers.py
from django import template

register = template.Library()

@register.simple_tag
def webp_image(image_field):
    """
    Returns the WebP URL if the image is local and a WebP version exists,
    otherwise returns the original URL.
    Usage: {% webp_image post.featured_image %}
    """
    if not image_field or not image_field.name:
        return ''

    url = image_field.url
    # Check if it's a local image (stored in media)
    if url.startswith('/media/'):
        # Get the model instance and look for the corresponding WebP spec field
        obj = image_field.instance
        # The spec field is named "featured_image_webp" (original field name + '_webp')
        webp_field_name = image_field.field.name + '_webp'
        if hasattr(obj, webp_field_name):
            webp_field = getattr(obj, webp_field_name)
            if webp_field and webp_field.url:
                return webp_field.url
    # Fallback to original URL (for external images or if WebP not available)
    return url