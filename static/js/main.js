// blog_project/static/js/main.js

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initMobileMenu();
    initImageLoading();
    initResponsiveFeatures();
    initAccessibilityFeatures();
    initPerformanceOptimizations();
    initTouchDevice();
    initFormValidation();
});

// Mobile Menu Functionality (from simple version)
function initMobileMenu() {
    const navToggler = document.querySelector('.navbar-toggler');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const navbarCollapse = document.querySelector('.navbar-collapse');

    // Close mobile menu when clicking a link
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 992 && navbarCollapse.classList.contains('show')) {
                const bsCollapse = new bootstrap.Collapse(navbarCollapse);
                bsCollapse.hide();
            }
        });
    });
}

// Image Loading - Enhanced version combining both approaches
function initImageLoading() {
    const images = document.querySelectorAll('img');

    images.forEach(img => {
        // Check if this is a lazy-loaded image
        if (img.hasAttribute('data-src')) {
            // For lazy-loaded images, use IntersectionObserver (from comprehensive version)
            if (!img.classList.contains('lazy-initialized')) {
                img.classList.add('lazy-initialized');

                // Add fade-in effect for lazy-loaded images
                img.style.opacity = '0';
                img.style.transition = 'opacity 0.3s ease-in-out';

                // Create observer for this image
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const targetImg = entry.target;
                            if (targetImg.dataset.src) {
                                targetImg.src = targetImg.dataset.src;
                            }
                            if (targetImg.dataset.srcset) {
                                targetImg.srcset = targetImg.dataset.srcset;
                            }
                            targetImg.classList.add('loaded');

                            // Trigger fade-in
                            setTimeout(() => {
                                targetImg.style.opacity = '1';
                            }, 100);

                            observer.unobserve(targetImg);
                        }
                    });
                }, {
                    rootMargin: '50px 0px',
                    threshold: 0.1
                });

                observer.observe(img);
            }
        } else {
            // For regular images, apply fade-in effect
            if (!img.complete) {
                img.style.opacity = '0';
                img.style.transition = 'opacity 0.3s ease-in-out';
                img.addEventListener('load', function() {
                    this.style.opacity = '1';
                });
                img.addEventListener('error', function() {
                    this.style.opacity = '1'; // Ensure it's visible even if there's an error
                });
            }
        }

        // Handle srcset cleanup for problematic images (from simple version)
        if (img.hasAttribute('srcset')) {
            const srcset = img.getAttribute('srcset');
            // Only remove problematic srcset if it contains specific patterns
            if (srcset.includes('-320w') || srcset.includes('-480w') || srcset.includes('-800w')) {
                // Check if the image has already errored or if we should remove srcset
                if (img.naturalHeight === 0 && img.naturalWidth === 0) {
                    img.removeAttribute('srcset');
                    img.removeAttribute('sizes');
                }
            }
        }
    });
}

// Touch device improvements (from simple version, enhanced)
function initTouchDevice() {
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

    if (isTouchDevice) {
        document.body.classList.add('touch-device');

        // Improve touch targets - more specific selector than comprehensive version
        const buttons = document.querySelectorAll('button:not(.navbar-toggler), .btn:not(.navbar-toggler), a.btn');
        buttons.forEach(btn => {
            if (btn.offsetHeight < 44 || btn.offsetWidth < 44) {
                btn.style.minHeight = '44px';
                btn.style.minWidth = '44px';
                btn.style.padding = '12px 16px';
            }
        });

        // Add hover effect removal for touch devices
        const hoverElements = document.querySelectorAll('.hover-effect, [class*="hover-"]');
        hoverElements.forEach(el => {
            el.classList.add('no-hover');
        });
    }
}

// Responsive Features (from comprehensive version, modified)
function initResponsiveFeatures() {
    // Responsive tables
    const tables = document.querySelectorAll('.table-responsive table');
    tables.forEach(table => {
        if (table.offsetWidth > table.parentElement.offsetWidth) {
            table.parentElement.classList.add('has-scroll');
        }
    });

    // Responsive images with srcset - only for images without srcset and not lazy-loaded
    const images = document.querySelectorAll('img:not([data-src]):not([srcset])');
    images.forEach(img => {
        if (img.src && !img.src.includes('-320w') && !img.src.includes('-480w') && !img.src.includes('-800w')) {
            const src = img.src;
            // Only add srcset for local images (not external URLs)
            if (src.startsWith('/') || src.includes(window.location.hostname)) {
                try {
                    const baseName = src.substring(0, src.lastIndexOf('.'));
                    const extension = src.substring(src.lastIndexOf('.'));

                    img.setAttribute('srcset',
                        `${baseName}-320w${extension} 320w, ` +
                        `${baseName}-480w${extension} 480w, ` +
                        `${baseName}-800w${extension} 800w`
                    );
                    img.setAttribute('sizes', '(max-width: 320px) 280px, (max-width: 480px) 440px, 800px');
                    img.loading = 'lazy';
                } catch (e) {
                    console.log('Could not generate srcset for:', img.src);
                }
            }
        }
    });
}

// Accessibility Features (from comprehensive version)
function initAccessibilityFeatures() {
    // Skip link focus
    const skipLink = document.querySelector('.sr-only-focusable');
    if (skipLink) {
        skipLink.addEventListener('focus', function() {
            this.classList.remove('sr-only');
        });

        skipLink.addEventListener('blur', function() {
            this.classList.add('sr-only');
        });
    }

    // ARIA labels for icons
    const iconButtons = document.querySelectorAll('button i, a i');
    iconButtons.forEach(button => {
        const icon = button.querySelector('i');
        if (icon && !button.getAttribute('aria-label')) {
            const iconClass = Array.from(icon.classList)
                .find(cls => cls.startsWith('fa-'))
                ?.replace('fa-', '') || 'icon';
            button.setAttribute('aria-label', iconClass + ' button');
        }
    });

    // Focus management for modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const focusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (focusable) focusable.focus();
        });
    });
}

// Performance Optimizations (from comprehensive version, enhanced)
function initPerformanceOptimizations() {
    // Connection-aware loading
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    if (connection) {
        if (connection.saveData) {
            // Reduce image quality for data saver mode
            document.body.classList.add('save-data');
            // Remove srcset for data saver mode
            document.querySelectorAll('img[srcset]').forEach(img => {
                img.setAttribute('data-original-srcset', img.getAttribute('srcset'));
                img.removeAttribute('srcset');
            });
        }

        if (connection.effectiveType && connection.effectiveType.includes('2g')) {
            // Disable animations for slow connections
            document.body.classList.add('slow-connection');
        }
    }

    // Cache frequently used elements
    window.blogElements = {
        nav: document.querySelector('nav'),
        mainContent: document.querySelector('main'),
        footer: document.querySelector('footer'),
        mobileMenu: document.querySelector('.navbar-collapse')
    };
}

// Form validation enhancement (from comprehensive version)
function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.setAttribute('novalidate', true);

        form.addEventListener('submit', function(e) {
            if (!this.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();

                // Focus first invalid field
                const invalidField = this.querySelector(':invalid');
                if (invalidField) {
                    invalidField.focus();
                    invalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }

            this.classList.add('was-validated');
        });
    });
}

// Enhanced error handling combining both versions
window.addEventListener('error', function(e) {
    // Image error handling (from simple version)
    if (e.target.tagName === 'IMG') {
        console.log('Image failed to load:', e.target.src);

        // If it's trying to load a responsive version, try loading the original
        const src = e.target.src;
        if (src.includes('-320w') || src.includes('-480w') || src.includes('-800w')) {
            const originalSrc = src.replace(/-320w|-480w|-800w/g, '').replace(/\.webp$/, '.jpg');
            e.target.src = originalSrc;
            return; // Prevent further error handling for image errors
        }
    }

    // General application error handling (from comprehensive version)
    console.error('Application error:', e.error);

    // Send to error tracking service (optional)
    if (window.Sentry) {
        Sentry.captureException(e.error);
    }
}, true);

// Offline detection (from comprehensive version)
window.addEventListener('online', function() {
    document.body.classList.remove('offline');
    showToast('Back online', 'success');
});

window.addEventListener('offline', function() {
    document.body.classList.add('offline');
    showToast('You are offline', 'warning');
});

// Toast notification system (from comprehensive version)
function showToast(message, type = 'info') {
    // Don't show toasts when offline (except for offline notification itself)
    if (navigator.onLine === false && type !== 'warning') return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="toast-body">
            ${message}
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    document.body.appendChild(toast);

    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initMobileMenu,
        initImageLoading,
        initTouchDevice,
        initResponsiveFeatures,
        initAccessibilityFeatures,
        initPerformanceOptimizations,
        initFormValidation,
        showToast
    };
}

