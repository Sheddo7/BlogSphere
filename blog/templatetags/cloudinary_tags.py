# blog/templatetags/cloudinary_tags.py - CREATE THIS FILE

from django import template
from django.conf import settings
import hashlib
import urllib.parse

register = template.Library()


@register.simple_tag
def cloudinary_url(image_url, width=None, height=None, quality=80, format='auto'):
    """
    Generate optimized Cloudinary URL for an image

    Usage:
        {% cloudinary_url post.image_url width=1200 height=675 %}
    """
    if not image_url or not settings.CLOUDINARY_CLOUD_NAME:
        return image_url

    # Build transformation parameters
    transformations = []

    if width:
        transformations.append(f'w_{width}')
    if height:
        transformations.append(f'h_{height}')

    transformations.append(f'q_{quality}')
    transformations.append(f'f_{format}')
    transformations.append('c_fill')  # Crop to fill dimensions

    transformation_string = ','.join(transformations)

    # Encode the original image URL
    encoded_url = urllib.parse.quote(image_url, safe='')

    # Build Cloudinary URL
    cloudinary_url = f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/image/fetch/{transformation_string}/{encoded_url}"

    return cloudinary_url


@register.simple_tag
def cloudinary_thumbnail(image_url, width=300, height=200, quality=80):
    """
    Generate thumbnail version of image

    Usage:
        {% cloudinary_thumbnail post.image_url width=300 height=200 %}
    """
    return cloudinary_url(image_url, width=width, height=height, quality=quality)


@register.simple_tag
def cloudinary_responsive(image_url, quality=80):
    """
    Generate responsive srcset for images

    Usage:
        {% cloudinary_responsive post.image_url %}

    Returns full img tag with srcset
    """
    if not image_url or not settings.CLOUDINARY_CLOUD_NAME:
        return f'<img src="{image_url}" alt="">'

    # Generate multiple sizes for responsive images
    sizes = [
        (400, '400w'),
        (800, '800w'),
        (1200, '1200w'),
        (1600, '1600w')
    ]

    srcset_parts = []
    for width, descriptor in sizes:
        url = cloudinary_url(image_url, width=width, quality=quality)
        srcset_parts.append(f'{url} {descriptor}')

    srcset = ', '.join(srcset_parts)

    # Default src (use 800px version)
    default_src = cloudinary_url(image_url, width=800, quality=quality)

    # Build img tag
    img_tag = f'<img src="{default_src}" srcset="{srcset}" sizes="(max-width: 768px) 100vw, 800px" loading="lazy" alt="">'

    return img_tag


@register.simple_tag
def cloudinary_placeholder(image_url, width=50, height=50, quality=20):
    """
    Generate tiny placeholder image for lazy loading

    Usage:
        {% cloudinary_placeholder post.image_url %}
    """
    return cloudinary_url(image_url, width=width, height=height, quality=quality, format='jpg')


@register.filter
def optimize_image(image_url, size='medium'):
    """
    Filter to optimize image with predefined sizes

    Usage:
        {{ post.image_url|optimize_image:"large" }}

    Sizes: thumbnail, small, medium, large, xlarge
    """
    sizes = {
        'thumbnail': (200, 150),
        'small': (400, 300),
        'medium': (800, 600),
        'large': (1200, 900),
        'xlarge': (1600, 1200)
    }

    if size not in sizes:
        size = 'medium'

    width, height = sizes[size]
    return cloudinary_url(image_url, width=width, height=height)