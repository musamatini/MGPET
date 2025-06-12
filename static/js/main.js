// static/js/main.js

document.addEventListener('DOMContentLoaded', function () {
    // Initialize AOS (Animate on Scroll) for general section reveals
    AOS.init({
        duration: 400, // Animation duration
        once: false,    // Animate elements only once
        offset: 200,    // Trigger animation a bit sooner 
    });

    // --- NAVBAR INITIAL ANIMATION (Only on homepage, once per session) ---
    const navbarElement = document.querySelector('.navbar'); // Select .navbar directly
    if (navbarElement) { // Check if navbarElement exists
        if (window.location.pathname === '/' && !sessionStorage.getItem('navbarAnimated')) {
            navbarElement.classList.add('navbar-is-animating-initial');
            sessionStorage.setItem('navbarAnimated', 'true'); // Set flag
        } else {
            // If not homepage or already animated, ensure it's immediately visible
            navbarElement.style.transform = 'translateY(0)'; 
            navbarElement.classList.remove('navbar-is-animating-initial');
        }
    }
    // --- END NAVBAR INITIAL ANIMATION ---

    // --- HERO SWIPER ---
    const heroSwiper = new Swiper('.hero-swiper', {
        effect: 'slide', 
        loop: true,
        autoplay: {
            delay: 6000, 
            disableOnInteraction: false,
        },
        speed: 900, 
        grabCursor: true,
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
            dynamicBullets: true, 
        },
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
        on: {
            init: function () {
                // Animate content of the initial active slide when Swiper is ready
                const activeSlideOnInit = this.slides[this.activeIndex];
                if (activeSlideOnInit) {
                    const caption = activeSlideOnInit.querySelector('.slide-caption');
                    if (caption) {
                        caption.classList.add('is-visible'); 
                    }
                }
            },
            slideChangeTransitionStart: function () {
                // Before a new slide starts its transition IN,
                // add 'is-visible' to ITSELF (the one becoming active).
                // Swiper's `this.activeIndex` already points to the destination slide index here.
                const nextActiveSlide = this.slides[this.activeIndex];
                if (nextActiveSlide) {
                    const caption = nextActiveSlide.querySelector('.slide-caption');
                    if (caption) {
                        caption.classList.add('is-visible');
                    }
                }

                // For all OTHER slides (especially the one transitioning OUT), 
                // remove 'is-visible' to reset their animation state.
                this.slides.forEach((slide, index) => {
                    if (index !== this.activeIndex) { // If it's not the incoming active slide
                        const caption = slide.querySelector('.slide-caption');
                        if (caption) {
                            caption.classList.remove('is-visible');
                        }
                    }
                });
            }
            // We don't need slideChangeTransitionEnd for this specific text animation logic
        }
    });

    // --- MOBILE MENU TOGGLE ---
    const menuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileNav = document.querySelector('.navbar-links-mobile');
    if (menuToggle && mobileNav) {
        menuToggle.addEventListener('click', () => {
            mobileNav.classList.toggle('active');
            const isExpanded = mobileNav.classList.contains('active');
            menuToggle.setAttribute('aria-expanded', isExpanded);
            menuToggle.querySelector('i').classList.toggle('fa-bars');
            menuToggle.querySelector('i').classList.toggle('fa-times');
        });
    }

    // --- SMOOTH SCROLL WITH NAVBAR OFFSET ---
    document.querySelectorAll('a[href^="#"], a[href*="/#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            const targetId = href.substring(href.lastIndexOf('#'));
            if (targetId.length > 1 && document.querySelector(targetId)) {
                if (window.location.pathname === '/' || href.startsWith('/#') || (href.startsWith('#') && window.location.pathname === '/')) {
                    e.preventDefault();
                    const targetElement = document.querySelector(targetId);
                    const navbarHeight = document.querySelector('.navbar')?.offsetHeight || 70; // Use actual height or fallback
                    
                    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                    const targetPositionInDocument = targetElement.getBoundingClientRect().top + scrollTop;
                    const offsetPosition = targetPositionInDocument - navbarHeight;

                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });

                    if (mobileNav && mobileNav.classList.contains('active')) {
                        mobileNav.classList.remove('active');
                        menuToggle.setAttribute('aria-expanded', 'false');
                        menuToggle.querySelector('i').classList.add('fa-bars');
                        menuToggle.querySelector('i').classList.remove('fa-times');
                    }
                }
            }
        });
    });

    // --- STICKY NAVBAR SCROLL EFFECT ---
    const navbarScrollEffect = document.querySelector('.navbar'); // Re-use navbarElement or query again
    if (navbarScrollEffect) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbarScrollEffect.classList.add('scrolled');
            } else {
                navbarScrollEffect.classList.remove('scrolled');
            }
        });
    }

    // --- ACTIVE NAV LINKS ---
    const navLinks = document.querySelectorAll('.navbar-links-desktop ul li a, .navbar-links-mobile ul li a');
    const currentPath = window.location.pathname;
    navLinks.forEach(link => {
        link.classList.remove('active');
        const linkHref = link.getAttribute('href');
        if (linkHref === currentPath || (linkHref !== '/' && currentPath.startsWith(linkHref) && linkHref.length > 1) ) {
            link.classList.add('active');
        } else if (currentPath === '/' && (linkHref === '/' || linkHref.endsWith('#home'))) {
             link.classList.add('active');
        }
    });

    // --- CTA SECTION EXPAND ANIMATION ---
    const ctaSection = document.querySelector('.cta-expand-reveal');
    if (ctaSection) {
        const ctaObserver = new IntersectionObserver((entries, observer) => { // Add 'observer' to the callback arguments
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target); // <<< STOP OBSERVING AFTER THE FIRST TIME
                }
                // REMOVE the 'else' block: entry.target.classList.remove('is-visible');
            });
        }, { threshold: 0.3 }); 
        ctaObserver.observe(ctaSection);
    }

});