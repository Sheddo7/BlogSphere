# blog/templatetags/image_optimizer.py - CREATE THIS FILE
"""
Template tags for automatic image optimization
Works with or without Cloudinary
"""

from django import template
from django.conf import settings
import os

register = template.Library()


@register.filter
def optimize_image(image_url, size='medium'):
    """
    Optimize image URL through Cloudinary CDN

    Usage in templates:
        {{ post.featured_image.url|optimize_image }}
        {{ post.featured_image.url|optimize_image:'large' }}
        {{ post.featured_image.url|optimize_image:'thumbnail' }}

    Sizes:
        - thumbnail: 320px wide
        - small: 640px wide
        - medium: 1024px wide (default)
        - large: 1920px wide
    """

    if not image_url:
        return ''

    # Get Cloudinary cloud name
    cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', '')

    # If Cloudinary not configured, return original URL
    if not cloud_name:
        return image_url

    # Define size transformations
    size_map = {
        'thumbnail': 'w_320,h_320,c_fill,q_auto:best,f_auto',
        'small': 'w_640,c_limit,q_auto:best,f_auto',
        'medium': 'w_1024,c_limit,q_auto:best,f_auto',
        'large': 'w_1920,c_limit,q_auto:good,f_auto',
        'original': 'q_auto:best,f_auto',
    }

    transformation = size_map.get(size, size_map['medium'])

    # Build Cloudinary fetch URL
    optimized_url = f"https://res.cloudinary.com/{cloud_name}/image/fetch/{transformation}/{image_url}"

    return optimized_url


@register.filter
def responsive_srcset(image_url):
    """
    Generate responsive srcset for images

    Usage:
        <img data-srcset="{{ post.image|responsive_srcset }}"
             sizes="(max-width: 768px) 100vw, 768px">
    """

    if not image_url:
        return ''

    cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', '')

    if not cloud_name:
        return f"{image_url} 1x"

    # Generate multiple sizes
    widths = [320, 640, 768, 1024, 1280, 1920]
    srcset_parts = []

    for width in widths:
        transform = f"w_{width},c_limit,q_auto:best,f_auto"
        url = f"https://res.cloudinary.com/{cloud_name}/image/fetch/{transform}/{image_url}"
        srcset_parts.append(f"{url} {width}w")

    return ', '.join(srcset_parts)


@register.simple_tag
def optimized_img(image_url, alt='', css_class='', lazy=True):
    """
    Generate complete optimized <img> tag

    Usage:
        {% load image_optimizer %}
        {% optimized_img post.featured_image.url alt=post.title css_class='img-fluid' %}
    """

    if not image_url:
        return ''

    cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', '')

    # Build image tag
    lazy_class = 'lazy-image' if lazy else ''
    src_attr = 'data-src' if lazy else 'src'

    if cloud_name:
        # Use Cloudinary with responsive images
        srcset = responsive_srcset(image_url)
        src = optimize_image(image_url, 'medium')

        img_tag = f'''<img {src_attr}="{src}" 
                          data-srcset="{srcset}"
                          sizes="(max-width: 768px) 100vw, 768px"
                          alt="{alt}"
                          class="{lazy_class} {css_class}"
                          loading="lazy">'''
    else:
        # No Cloudinary, use original
        img_tag = f'<img {src_attr}="{image_url}" alt="{alt}" class="{lazy_class} {css_class}" loading="lazy">'

    return img_tag


@register.inclusion_tag('blog/components/optimized_card_image.html')
def card_image(image_url, alt='', aspect_ratio='16-9'):
    """
    Render optimized card image with aspect ratio wrapper

    Usage:
        {% load image_optimizer %}
        {% card_image post.featured_image.url alt=post.title aspect_ratio='16-9' %}
    """

    return {
        'image_url': image_url,
        'optimized_url': optimize_image(image_url, 'medium'),
        'srcset': responsive_srcset(image_url),
        'alt': alt,
        'aspect_ratio': aspect_ratio,
    }