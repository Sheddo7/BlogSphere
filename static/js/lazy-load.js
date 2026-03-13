/* ============================================================
   LAZY LOADING IMAGES - JAVASCRIPT
   Add this to: static/js/lazy-load.js
   ============================================================ */

(function() {
    'use strict';

    /**
     * Lazy Load Images using Intersection Observer API
     * Falls back to immediate loading if API not supported
     */

    // Configuration
    const config = {
        rootMargin: '50px 0px', // Load images 50px before they enter viewport
        threshold: 0.01,
        enableBlurUp: true
    };

    /**
     * Load image and handle success/error states
     */
    function loadImage(img) {
        const wrapper = img.closest('.lazy-image-wrapper');
        const src = img.dataset.src;
        const srcset = img.dataset.srcset;

        if (!src) return;

        // Create new image to preload
        const tempImage = new Image();

        tempImage.onload = function() {
            // Set the actual image sources
            img.src = src;
            if (srcset) {
                img.srcset = srcset;
            }

            // Add loaded class with slight delay for animation
            setTimeout(() => {
                img.classList.add('loaded');
                if (wrapper) {
                    wrapper.classList.add('loaded');
                }
            }, 50);

            // Remove data attributes to save memory
            delete img.dataset.src;
            delete img.dataset.srcset;
        };

        tempImage.onerror = function() {
            console.error('Failed to load image:', src);
            if (wrapper) {
                wrapper.classList.add('error');
                wrapper.classList.remove('loading');
            }
        };

        // Start loading
        if (wrapper) {
            wrapper.classList.add('loading');
        }
        tempImage.src = src;
        if (srcset) {
            tempImage.srcset = srcset;
        }
    }

    /**
     * Initialize Intersection Observer
     */
    function initIntersectionObserver() {
        const imageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    loadImage(img);
                    observer.unobserve(img);
                }
            });
        }, config);

        // Observe all lazy images
        const lazyImages = document.querySelectorAll('.lazy-image[data-src]');
        lazyImages.forEach(function(img) {
            imageObserver.observe(img);
        });

        return lazyImages.length;
    }

    /**
     * Fallback for browsers without Intersection Observer
     */
    function fallbackLazyLoad() {
        const lazyImages = document.querySelectorAll('.lazy-image[data-src]');

        function loadVisibleImages() {
            lazyImages.forEach(function(img) {
                if (img.dataset.src) {
                    const rect = img.getBoundingClientRect();
                    const isVisible = (
                        rect.top >= -50 &&
                        rect.left >= -50 &&
                        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) + 50 &&
                        rect.right <= (window.innerWidth || document.documentElement.clientWidth) + 50
                    );

                    if (isVisible) {
                        loadImage(img);
                    }
                }
            });
        }

        // Check on scroll and resize
        let scrollTimeout;
        window.addEventListener('scroll', function() {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(loadVisibleImages, 100);
        }, { passive: true });

        window.addEventListener('resize', loadVisibleImages, { passive: true });

        // Initial check
        loadVisibleImages();

        return lazyImages.length;
    }

    /**
     * Initialize lazy loading
     */
    function init() {
        // Check if Intersection Observer is supported
        if ('IntersectionObserver' in window) {
            const count = initIntersectionObserver();
            console.log(`🖼️ Lazy loading initialized for ${count} images (Intersection Observer)`);
        } else {
            // Fallback for older browsers
            const count = fallbackLazyLoad();
            console.log(`🖼️ Lazy loading initialized for ${count} images (Fallback)`);
        }
    }

    /**
     * Public API for dynamically loaded content
     */
    window.LazyLoad = {
        init: init,
        loadImage: loadImage,
        refresh: function() {
            init();
        }
    };

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

/* ============================================================
   USAGE EXAMPLES:

   1. Basic lazy image:
   <div class="lazy-image-wrapper">
       <img class="lazy-image"
            data-src="path/to/image.jpg"
            alt="Description">
   </div>

   2. With aspect ratio (prevents layout shift):
   <div class="lazy-image-wrapper aspect-ratio-box aspect-ratio-16-9">
       <img class="lazy-image"
            data-src="path/to/image.jpg"
            alt="Description">
   </div>

   3. With responsive srcset:
   <div class="lazy-image-wrapper">
       <img class="lazy-image"
            data-src="path/to/image.jpg"
            data-srcset="image-320.jpg 320w, image-640.jpg 640w, image-1024.jpg 1024w"
            sizes="(max-width: 640px) 100vw, 640px"
            alt="Description">
   </div>

   4. Refresh after AJAX load:
   window.LazyLoad.refresh();

   ============================================================ */